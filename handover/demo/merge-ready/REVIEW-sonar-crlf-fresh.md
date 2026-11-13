# Review: sonar-yaml-fix.patch and crlf-guard-v2.patch on pr-3-tests 2db3926
Reviewer: fresh, independent, shell. Scratch dir /tmp/work/rv-3126. Read-only clone (no push). Made-up data only. Head checked out: 2db3926 (HEAD log line confirmed). Model: Sonnet 5.5.

## Failures and gaps (lead with these)
1. PREAMBLE rule 8 command does not work in this repo: `uv run --all-extras --group test pytest` fails with "Group `test` is not defined in the project's `dependency-groups` table". I used the venv the repo's own lint.yml uses instead: `uv venv --python 3.12` + `uv pip install --require-hashes -r requirements-dev.txt`, then plain ruff/mypy/bandit/pytest. Gitleaks 8.30.1 (CI's pinned version, SHA-256 checked equal to lint.yml's) on PATH via GITLEAKS_BIN, DPLD_REQUIRE_SCAN=1, DPLD_REQUIRE_DEMO=1.
2. Full pytest suite of the combined tree did NOT finish: I stopped it after about 12 minutes (it spawns sub-pytests). NOT claimed. What I did run on the combined tree: 133 passed (tests/test_hygiene.py, test_workflow_files_parse.py, test_nosemgrep_form.py, test_gitleaks_semgrep_lock.py, test_gitleaks_exceptions.py).
3. crlf-guard-v2: five of nine mutants SURVIVE (details in section B5). Weakest points: nothing tests the hint inside the real scan failure message (M3, M8), nothing tests the text of the cure (M6), and the new guard test cannot fail on its own on an LF tree if it is emptied (M5). Lone CR (no LF) is not detected (M9).
4. EGM skills: I cannot run egm:* from this shell session as a reviewer; per rule 13 this is an evidence run only, the lead runs the EGM step. Rule 1 (bible RULES.md under <studio>) is not reachable from here (no studio folder); no R-numbers were looked up. R-numbers cited: none (only rule numbers of the preamble: 6, 8, 12, 13, 19).
5. Not checked: real Windows, real GitHub Actions run of sonar.yml (only static parse and actionlint 1.7.12), nested requirements-*.txt, a CRLF blob committed in history (cure via `git checkout -- file` would then not help; not tested).

## A. sonar-yaml-fix.patch
| Check | Command | Measured |
|---|---|---|
| A1 apply check | `git apply --check sonar-yaml-fix.patch` on 2db3926 | OK; `git apply` OK; status: M sonar.yml, ?? tests/test_workflow_files_parse.py |
| A2 YAML parse before | PyYAML 6.0.3 `safe_load` on each .github/workflows/*.yml | codeql OK, lint OK, sonar.yml ERR "mapping values are not allowed here ... line 45, column 71" (the `--only-binary=:all: -r` colon-space) |
| A2 after patch | same | codeql, lint, sonar all OK (semgrep.yml from the semgrep patch also OK in the combined tree) |
| A3 new test | `pytest tests/test_workflow_files_parse.py -q` | 4 passed |
| A4 revert only sonar.yml | restore original sonar.yml, keep test | 1 failed (sonar.yml: "not valid YAML ... line 45, column 71"), 3 passed. Test restored afterwards. |
| A5 CI lint steps | `ruff check .`, `ruff format --check .`, `mypy --platform linux`, `mypy --platform win32`, `bandit -ll -r src tools scripts -c pyproject.toml` | All checks passed; 146 files formatted; mypy no issues in 26 files (both platforms); bandit exit 0 (no medium/high severity) |
| A6 wider workflow check | `actionlint 1.7.12` (installed via PyPI actionlint-py) on all workflows | Patched tree: no findings, exit 0. Original sonar.yml: `sonar.yml:45:70: could not parse as YAML` (only that). Combined tree incl. semgrep.yml: no findings. |
No other workflow-level mistakes found in codeql.yml, lint.yml, sonar.yml (checked by actionlint: step keys, expression syntax, contexts, job keys). I did not verify action SHAs against GitHub (not checked).

Limits of the new test (measured with mutants of sonar.yml, PyYAML test vs actionlint):
| Mutant | New test | actionlint |
|---|---|---|
| `runs-on` -> `run-on` (line 29) | passes (MISSED) | caught: "runs-on section is missing" |
| `if:` with `=` operator (line 32) | passes (MISSED) | caught: expression error line 32 |
| `uses:` -> `use:` on a step (line 38) | caught (1 failed) | caught |
| `runner.os` -> `runnr.os` (lines 56,57) | passes (MISSED) | caught: undefined variable |
So the test fixes the reported YAML syntax class only; GitHub-expression and key-name mistakes need actionlint (it is free, static, and was clean). Suggestion: add actionlint as a CI step or accept the limit knowingly.

## B. crlf-guard-v2.patch
B1 apply: alone on 2db3926 OK. Orders on fresh clones: v2 alone; v2,sonar,versions,semgrep-v4; semgrep-v4,versions,sonar,v2; sonar,v2; semgrep,v2; v2,semgrep: all applied without error. Resulting tree of the two 4-patch orders: `diff -r` identical.
B2 tests: v2 alone: `pytest tests/test_hygiene.py` 18 passed (base 15 passed, +3 new). ruff check, ruff format --check, mypy linux and win32 clean on v2 tree. Combined tree: 133 passed in the five files above; ruff/format/mypy clean (145 files).
B3 CRLF copy: `sed -i 's/$/\r/' sonar-project.properties` (file reports "CRLF line terminators"). Result: 2 failed, 16 passed. test_hygiene_scan_public fails with "gitleaks dir reported findings; files: ['sonar-project.properties']" followed by the line "sonar-project.properties: this file has Windows line endings (CRLF); ... save it with LF, or discard your edits to it with: git checkout -- <file>". test_the_secret_scan_files_have_no_carriage_return fails with the same hint.
B4 cures (each starting from the same CRLF file, CR lines counted with grep):
- `git add --renormalize .`: CR count stays 14, tests 2 failed. Does NOT cure (as the docs sentence says).
- `git checkout -- sonar-project.properties`: CR 0, 18 passed. Cures.
- `sed -i 's/\r$//' sonar-project.properties`: CR 0, 18 passed, git status clean for the file. Cures.
B5 mutants (a1 tree; each run twice: LF tree and CRLF sonar file; "caught" = at least one unmodified test fails on the LF tree):
| Mutant | LF tree | CRLF tree | Verdict |
|---|---|---|---|
| M1 CR check disabled (`if False:`) | 2 failed (both helper tests) | 3 failed | CAUGHT |
| M2 sonar-project.properties dropped from LF_ONLY_FILES | 1 failed (empty-list assertion) | 2 failed | CAUGHT |
| M4 `.properties` exempt like .ps1 | 1 failed (scan-failure helper test) | 2 failed | CAUGHT |
| M7 exemption widened to .ps1/.properties/.txt/.toml | 2 failed | 3 failed | CAUGHT |
| M3 hint removed from the real scan failure message | 18 passed | 2 failed, hint printed once instead of twice | SURVIVES |
| M5 guard test body replaced by `pass` | 18 passed | 1 failed (only gitleaks test) | SURVIVES |
| M6 hint text changed to recommend `git add --renormalize .` (wrong cure) | 18 passed | 2 failed | SURVIVES |
| M8 flagged-file list always empty (hint and file names lost in scan message) | 18 passed | 2 failed | SURVIVES |
| M9 detects only the pair CR LF, not a lone CR | 18 passed | 2 failed | SURVIVES (a lone CR file is not flagged) |
Note: on a CRLF tree the whole suite fails anyway (gitleaks reports the key line), so the guard's value is the message; the surviving mutants are exactly the message content and the guard test itself.
Suggested fixes (not applied; patches were read-only for me): add one end-to-end test that plants a CRLF sonar-project.properties in a tmp copy, runs the scan failure path, and asserts the message holds the file name and `git checkout -- ` plus `sed -i`; assert the cure text does not contain "renormalize" except in the negative sentence; add a lone-CR case if wanted.

## Files / head
Report: /tmp/work/rv-report-sonar-crlf.md. Scratch: /tmp/work/rv-3126 (repo, a1..a6, v venv, gl gitleaks). Head under test: 2db3926 (no commits made, nothing pushed). Processes: the one full-suite pytest I started was stopped; no other background process left. Token use: not measured.
