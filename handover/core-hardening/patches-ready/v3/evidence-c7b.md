# Evidence C7b (EVIDENCE RUNNER: records only, no judgement)
Date 2026-11-16. Raw logs: `raw-c7b/`. Scratch trees: `/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/c7b/{base,patched,nohandover_copy}`.

## Deviations from the brief (read first)
1. `git archive b4cce5b` does NOT exclude `handover/`: that commit tracks `handover/` (top level lists it). Both trees therefore contain `handover/`.
2. Because of (1), full suite fails 2 tests on BOTH unpatched and patched trees (see below). I added an extra run: patched tree with `handover/` removed (`nohandover_copy`).
3. `bandit` is not installed and `uv run ... bandit` fails ("Failed to spawn bandit"; logs `*-bandit.log`, `patched-bandit-version.log`). I used `uvx bandit@1.8.6 -ll -r src` instead (version 1.8.6, from PyPI, unpinned by the repo).
4. The shell env contained AWS_* variables (harness). My first launch inherited them; I killed it (processes I started), deleted its logs, and relaunched with AWS_*, AZURE_*, GOOGLE_APPLICATION_CREDENTIALS, ANTHROPIC_API_KEY unset. Not a literal `env -i`: PATH/HOME and UV vars kept.
5. `patch` left `src/hadavin_sdk/backends/table.py.orig` (A-01 applied hunk #1 with offset 5 lines; "succeeded at 196"). I deleted the .orig only after the full suite runs, before the new-tests-only run. No fuzz reported, no rejects.

## Step 1-2
- `git cat-file -t b4cce5b` -> `commit`. Trees: `git archive b4cce5b` extracted, `git init`, local identity, `git add -A`, `git commit`.
- sha256 of the three patches equals SHA256SUMS.txt: C-01 fddf8a15...68adcf, A-01 092d673a...7986c, G5-wording 0815212a...089d (all 3 match).
- `uv --version`: uv 0.11.32. `bandit --version` (system): command not found; uvx bandit 1.8.6 (python 3.13.18).

## Step 3 patch application (patch -p1, tree = clean base)
dry-run each alone: C-01 rc=0, A-01 rc=0, G5-wording rc=0. Dry-run then real apply in order C-01, A-01, G5-wording: all rc=0 (logs `raw-c7b/apply-*.log`). Files changed: 11 modified src files, 3 modified tests, new `audit/spill.py`, `tests/test_a01_audit_reconcile.py`, `tests/test_c01_route_limits.py`.

## Step 4 patched tree, with handover/ present
- `ruff check`: All checks passed, rc=0. `ruff format --check`: 302 files already formatted, rc=0.
- `bandit -ll -r src` (uvx 1.8.6) patched: rc=0, Medium 0, High 0 (Low 5). Same counts on base (`base-bandit-uvx.log`).
- Full pytest (`-q -p no:cacheprovider`, 4 min): **2 failed, 9489 passed, 455 skipped**, PYTEST_RC=1.
  Failed: `tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked` (a file under handover/ holds a vendor string; one handover file is not UTF-8) and `tests/test_repo_rules.py::test_licences_are_proprietary` (handover/promotion-inputs/... LICENSE files are not the proprietary text).
- Extra run, patched tree with `handover/` removed (committed): **1 failed, 9490 passed, 455 skipped**, rc=1. The failure is `tests/test_s4_llm_guard.py::test_ids_and_plan_hashes_survive_redaction` (random-id test, see below). The two handover-related failures did not occur.

## Step 5 baseline (unpatched, handover/ present)
ruff check/format rc=0. Full pytest: **2 failed, 9389 passed, 455 skipped**, rc=1; the same two tests fail. Difference patched minus base: +100 passed, 0 extra failures (tests added by patches).

## Intermittent failure (s4)
That test builds random ids and passes them through `approvals.channel.clean`; the failing run shows `pln-...` replaced by "[command withheld (G4)]". `channel.py` is not touched by any patch. Repeat: test alone 40 times each on patched and base: 0 failures / 40 each (`flaky-s4-repeat.log`). In-process loop of the same logic, 20000 iterations: base 9 bad, patched 3 bad (`flaky-s4-loop.log`). So the intermittent failure exists on the unpatched code too (about 0.015-0.045 percent per run); I did not diagnose its cause or fix it.

## Step 6 new tests only (patched tree, verbose; `patched-newtests-verbose.log`)
95 passed, 0 failed, 0 skipped. `tests/test_a01_audit_reconcile.py` 34 passed; `tests/test_c01_route_limits.py` 61 passed.

## Step 7 banned vendor word
Searched every file in raw-c7b/ and this file with the BANNED tuple (10 terms). Found 4 hits each in `base-pytest.log` and `patched-pytest.log` (from the failure message text); redacted in place with `[BANNED-WORD-REDACTED]`. Recount: 0. (Pytest line counts and rc unchanged.) Note: pytest logs were redacted after the runs; the original failure text is therefore not byte-exact.

## Processes
Started by me: run.sh chain, 2 pytest suites + extra, loops, uvx. All finished; 0 left running. A first launch with AWS_* env was killed (pkill by exact pattern). Unrelated processes of another agent (a mutation run in a `c5v5` scratch dir) are running; I did not touch them.

## Last lines
patched-pytest.log: `2 failed, 9489 passed, 455 skipped in 240.40s (0:04:00)` / `PYTEST_RC=1`
base-pytest.log: `2 failed, 9389 passed, 455 skipped in 239.44s (0:03:59)` / `PYTEST_RC=1`
patched-nohandover-pytest.log: `1 failed, 9490 passed, 455 skipped in 229.33s (0:03:49)` / `PYTEST_RC=1`
