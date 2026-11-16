# A24 PR91 fix batch 2: builder report (head db0e0cee6c7e89fbc1656a7d9119f66bac13d86b, branch core/ci-scan-config-guard-fix1)

## What failed, what is uncertain, what I did not check (first)
- Not checked: CI on GitHub (CodeQL, SonarCloud, CodeRabbit, the real `check`/`security` jobs). Only local runs below. No fresh independent review has run (cap rule: security path, a new round is needed).
- UNVERIFIED: the CODEOWNERS handle `@veerarakesh56` (kept as it was). GitHub also does not count a self-approval; the ruleset is owner-only and not done. The list and the code owners file stay "a review aid, not a lock".
- Item 9 (lead decision needed): `tests/demo_askdata/corpus.py` keeps its file-level marker. Exact text: `# ruff: noqa: S608, ISC004  # SQL text is the test data; implicit concatenation keeps long statements readable`. It names codes only (not blanket). Removing it gives 188 ruff findings (S608 on test SQL lines plus ISC004), so I did not narrow it. It is on the list with that reason. Decision for the lead: accept it, or have me add 188 per-line markers.
- Honest note on my own slip: my first mutation run passed vacuously (the script copy could not find `tests/test_no_reference_material.py`, so every mutant "failed" for an unrelated reason). The control test caught it; I fixed `_place` and re-ran.
- Known remaining gaps from the r2 nits, not fixed: a marker moved onto other code with identical text is not seen (documented, test pins it); the root-pyproject pin lives in a PR-controlled test file (needs the owner ruleset); symlinked configs are hashed by target; bash/sh are not vouched by the CI step (stated in ci.yml). All three need the owner ruleset or are by design.

## Items (BL-core-a24-r2-01..08)
1. Case: every SUPPRESSIONS regex compiled with `re.IGNORECASE`. Tests: upper and mixed case per original rule (NOQA, NoQA: S101, noqa: s101, NOSEC, NOSEMGREP, GITLEAKS:ALLOW, TRIVY:IGNORE, RUFF: NOQA).
2. Markers: new rules suppress-nosonar, -lgtm, -codeql, -zizmor-ignore, -allowlist-secret (also nextline, whitelist), -nopmd, -checkov-skip, -tfsec-ignore, -ruff-range (disable/ignore/enable). The semgrep ignore is matched without a comment prefix; nosec no longer needs a trailing word boundary. Rule renamed `suppress-nosemgrep` -> `suppress-semgrep-ignore` (the old rule name itself would now hit in the list file). Each rule has hit and no-hit cases (NEW_HITS, NEW_MISSES). Marker words are built from parts in the script and the tests. First scan found 5 real NOSONAR markers (cli.py x2, k1b/score.py x3, all `S8707` on operator CLI paths): listed with a reviewed reason.
3. Configs: every below-root `pyproject.toml` is a hash-pinned scanner config and fails (`nested-pyproject-scanner-table`, not listable) if it holds `[tool.ruff`, `[tool.bandit` or `[tool.semgrep`. New names (compared in lower case): .flake8, mypy.ini, sonar-project.properties, .sonarcloud.properties, .coderabbit.yaml/.yml, .semgrep.yml/.yaml, trivy.yml, .pre-commit-config.yaml, .secrets.baseline, .snyk; folders `.github/codeql/` and `.semgrep/`. Two existing real files now pinned: `.coderabbit.yaml`, `.sonarcloud.properties`. I did not hash-pin the whole `.github/` tree (the design reviewer's recommendation): not done, it needs your call. Negative test: nested pyproject with a ruff ignore fails even when pinned.
4. NUL fails closed: a NUL anywhere in a file whose extension is not on BINARY_EXTENSIONS (images, archives, fonts, whl, parquet, db, bin, ...) is `nul-in-text-file`, and the file is still scanned as text. Tests: AWS example key behind a NUL in x.env, Dockerfile, x.html (plus Makefile, a.conf, x.pyi, c.go; NUL past byte 8000); a real key behind a NUL is also found; known binary formats still pass. A NUL in a pinned config is now also refused (an older test changed accordingly).
5. Reasons: a reason starting with `NEW` (word) or shorter than 15 characters is refused. `--print-list` output is rejected by the scan until reviewed (test). Plus an extra unlistable rule `file-noqa-without-codes` for a file-level `ruff:/flake8: noqa` without codes.
6. CODEOWNERS: added /tests/test_scan_repo.py, /tests/test_scan_repo_mutations.py, /tests/test_ci_gitleaks_scope.py, /tests/test_ci_toolpath_step.py, /pyproject.toml, /uv.lock; handle unchanged and unverified.
7. CHANGELOG entry rewritten to match the code (count@sha256, `--print-list`, NUL refusal, markers, config set, glob refusal, list-file pins, "review aid until the owner's ruleset exists"). Written without literal markers, since the semgrep ignore word now hits without a prefix.
8. ci.yml: comment reworded (`--no-build` blocks sdist builds only; a wheel can run a .pth at start; the lock hashes are the control). Run text unchanged, so the golden file was not regenerated; the two CI tests pass (196 passed).
9. File-level noqa: all three named codes only. `fuzzgen.py` (S608, S311) narrowed to 5 per-line noqa (ruff `--add-noqa`, then `ruff format`); `test_validate_harm.py` (S608) narrowed to 1 per-line noqa; `corpus.py` left (above). The scan now refuses a file-level noqa without codes (test).
10. Mutation checks: `tests/test_scan_repo_mutations.py` plants 8 weakenings in a temp copy (NUL skip moved before the checks, hash check dropped, glob check dropped, IGNORECASE removed, reason check dropped, nested-pyproject check dropped, blanket file-noqa check dropped, NUL allowed for every extension) and asserts tests/test_scan_repo.py fails on each; a control on the unchanged copy must pass. Raw output: handover/reports/A24-PR91-fix2-mutation-output.txt (9 passed in 214 s). Cost: about 3.5 minutes added to the full suite.

## Evidence (commands and results, worktree /home/user/build/WT-A24)
- `ruff check src tests demos tools`: All checks passed (rc 0). `ruff format --check`: 319 files already formatted (rc 0). `bandit -ll -r src tools`: rc 0.
- `python tools/scan_repo.py`: rc 0 (list regenerated with `--print-list`, the 5 new/changed reasons written by hand after reading each file).
- `pytest tests/test_scan_repo.py` (incl. test_the_real_repo_passes_with_its_own_list): 237 passed, rc 0. `pytest tests/test_ci_gitleaks_scope.py tests/test_ci_toolpath_step.py`: 196 passed. `pytest tests/test_scan_repo_mutations.py`: 9 passed.
- Full suite once via heavy.sh (log /tmp/a24fix2-full.log, no PG DSN set): 10382 passed, 455 skipped in 458 s, exit=0.
- Not run before the change: a fail-before run of the new tests against the old script. The mutation tests cover the main fixes instead; the new-rule hit cases fail on the old script by construction (rules absent).

## Files changed (9)
.github/CODEOWNERS, .github/workflows/ci.yml (comment), CHANGELOG.md, tests/demo_askdata/fuzzgen.py, tests/demo_askdata/test_validate_harm.py, tests/test_scan_repo.py, tests/test_scan_repo_mutations.py (new), tools/scan_repo.py, tools/scan_suppressions.txt.

## Least privilege
No identity, role or credential touched. The scan reads tracked files only; the mutation tests write only into pytest temp folders.

## Hygiene
No sub-agents. One background full-suite run, finished. One earlier background mutation run, finished. No process left running. Not committed in the handover branch (this report and the mutation output are untracked files there). Pushed only to origin core/ci-scan-config-guard-fix1.

Head SHA: db0e0cee6c7e89fbc1656a7d9119f66bac13d86b
