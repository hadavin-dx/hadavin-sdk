# NOTES: no-demo patches v3 (client copy = demo_only/ deleted)

Base db54e13. Studio rules: R6 (failures first), R7 (class level, mutants), R19 (one pytest process at a time; I stopped everything I started). EGM not run by me (lead's step). Nothing pushed. Answers rv18 (/tmp/work/rv18-report.md). Replaces nodemo-fix-v2, nodemo-optional-hygiene-repo-v2, nodemo-ci-job (v1/v2). nodemo-ruff-isort.patch is UNCHANGED (byte-identical, diffed).

## What failed or is limited (first)
- My first CI-job gate test was wrong twice, found and fixed before reporting: (a) my test double (shim python) intercepted every run when SHIM_MODE was unset, so the first 4 "real" mutants (crash, failed, error, exit) did not run real pytest; (b) a second job run overlapped the first and polluted the shared summaries file (a "10 lines" message). Both were rerun alone, one process at a time; the table below is that clean rerun. (c) My first O7 test skipped instead of failing under the mutant (a skip is green): rewritten with `assert not _skipped(...)`, then O7 died.
- nodemo-optional-hygiene-repo-v3.patch no longer applies on db54e13 alone (v2 did): its new test sits next to P1's helper code. It must be applied AFTER sonar-p1-quickwins-v3.1 (as you said). The other three apply on db54e13 alone.
- The CI job was NOT run on a GitHub runner. Each `run:` block was run locally as `bash -e <block>` (GitHub's default shell form `bash -e {0}`, no pipefail; the v2 notes claimed `-o pipefail`, wrong, now removed), Python 3.13 locally (the job uses 3.12), venv from requirements-dev.txt. The gitleaks download/checksum step was not run (offline binary used); actionlint not installed, so the file is checked by yaml.safe_load plus the repo's workflow tests (all pass).
- The floor and the skip budget are measured on Python 3.13 on this machine; a 3.12 runner may differ by a few. I put a margin (floor 988-18, budget 80+5), so a first real run could still be red for that reason alone: then adjust the two numbers, not the logic.
- Pre-existing, found while measuring: in the no-demo copy 74 of the 80 skips are "needs the demo_only folder" (68 test files that conftest.py replaces by ONE placeholder item each, 6 tests that reach the folder at run time). So the no-demo job runs far fewer tests than the demo-present suite; the gate cannot change that, it only pins it.
- A leftover `demo_only/__pycache__` (from running tests before the cut) keeps the folder alive; the job's "Delete" step then fails loudly ("still there"). I hit it myself when I copied a tree; CI checkouts are fresh.
- Not run: Windows, Python 3.12, browser tests, the full suite with demo present (affected files only: 218 passed).

## (1) nodemo-fix-v3.patch (tests/test_except_clause_hierarchy.py)  MAJOR 2 closed
`_present(rows, demo_gone: bool)` now takes the flag; it is computed once at module level (`DEMO_GONE = not (REPO / "demo_only").is_dir()`) and passed at the three call sites (HANDLERS twice, RERAISE, STILL_CAUGHT). Two new tests (3 test items: one parametrized over demo_gone True/False):
- `test_present_skips_only_demo_rows_and_only_when_the_folder_is_gone[True|False]`: five invented rows (two product rows, two under demo_only/, one `demo_onlyx/` look-alike); the skip condition must be exactly `[False, False, demo_gone, demo_gone, False]`, as real bool.
- `test_demo_gone_is_the_state_of_the_folder_and_every_guarded_test_uses_it`: DEMO_GONE agrees with a different probe (`.exists()`), and for every real parameter of the four guarded tests (read from their parametrize marks) the skip condition is `DEMO_GONE and path starts with demo_only/`; exactly six demo rows exist (not vacuous), and product rows exist.
Mutants (reviewer's G1-G8 plus two of mine) on the whole file, demo present (DPLD_REQUIRE_DEMO=1) and demo deleted; v2 column from the reviewer's table (/tmp/work/rv18-1/mut-guard.txt); evidence-nodemo3-1-guard-mutants.txt:
| mutant | v2 result (reviewer) | v3 demo present | v3 demo deleted | verdict |
|---|---|---|---|---|
| G1 skip product rows too | green (5 passed, 44 skipped) | 1 failed | 2 failed | KILLED |
| G2 always gone (a: DEMO_GONE=True; b: _present ignores its argument) | green | a: 1 failed; b: 2 failed | a: green (identical to real when folder is gone); b: 1 failed | KILLED (a only where it differs from reality: demo present) |
| G3 `or` instead of `and` | green | 3 failed | 3 failed | KILLED |
| G4 never skip | killed | 1 failed | 8 failed | killed |
| G5 wrong folder name | killed | 2 failed | 8 failed | killed |
| G6 prefix without "/" | equivalent (rv18) | 1 failed | 1 failed | now KILLED (the look-alike `demo_onlyx/` row) |
| G7 `.is_file()` on the folder | green | 1 failed | green (same as real when gone) | KILLED where it differs (demo present) |
| G8 probe fakes.py instead of the folder | equivalent (rv18) | 52 passed | 46 passed, 6 skipped | equivalent: same result unless the folder exists without fakes.py (then the folder test would differ only in a half-deleted tree) |
| G9 (mine) call site passes False | n/a | equivalent (demo present: False anyway) | 3 failed | KILLED where it differs |
G1, G2, G3, G7 (the four you required) all die. G8 stays equivalent by construction.
Real behaviour unchanged: demo present 52 passed (49 old + 3 new items); demo deleted 46 passed, 6 skipped, the 6 skips are the six named demo rows (evidence-nodemo3-8...).

## (2) nodemo-optional-hygiene-repo-v3.patch (tests/test_hygiene.py, tests/test_no_placeholders.py)  rv18 minor 2 closed
The code of v2 was already right (`.exists()`, `cwd == REPO`). Chosen against `git rev-parse --is-inside-work-tree`: that command also says "yes" for an archive unpacked INSIDE another repository, which would then list the wrong repository's files; the plain test "REPO has its own .git, folder or file" is the exact question. New test `test_git_work_tree_skip_is_for_this_repository_only_and_accepts_a_git_file`: REPO is pointed (monkeypatch of the module name) at folders made in tmp: one without .git (must skip, also through `_git(REPO, ...)`), one with a `.git` folder (no skip), a REAL linked worktree made with `git worktree add` whose `.git` is asserted to be a FILE (no skip, git works); and a call about another folder than REPO must never skip even when REPO has no .git. Set-up runs with REPO pointed at the .git-folder dir so the helper cannot skip its own set-up. A submodule has the same `.git`-file shape as the worktree. Mutants (evidence-nodemo3-2-optional-mutants.txt; B = demo deleted git copy, C = demo deleted no-.git copy):
| mutant | B (git copy) | C (no .git) |
|---|---|---|
| O1 helper never skips | 1 failed | 6 failed |
| O2 _git does not call helper | 1 failed | 5 failed |
| O3 scan test does not call helper | equivalent in a git copy (108 passed) | 1 failed |
| O4 `.git` must be a directory | **1 failed (was green in v2)** | **1 failed** |
| O5 REPO one level too low | 8 failed | 8 failed |
| O6 helper inverted | 1 failed | 6 failed |
| O7 `_git` skips for any folder | **1 failed (was green)** | **1 failed (was green)** |
| O8 `.git` must be a file (mine) | 1 failed | 1 failed |
Baselines: B 108 passed; C 102 passed, 6 skipped (5 + 1, all named). The planted-literal trade of v2 (no-git copy cannot scan) is unchanged and stated.

## (3) nodemo-ruff-isort.patch: unchanged.

## (4) nodemo-ci-job-v3.patch (OPTIONAL; new file .github/workflows/nodemo.yml)  MAJOR 1 closed
Changes against v2 (pins, permissions, gitleaks install, ruff step, delete step are as before):
1. Each chunk: `python -u -m pytest ... | tee chunk.txt` then `rc=${PIPESTATUS[0]}` as the very next command; works under `bash -e` WITHOUT pipefail (a comment in the file says so; no pipefail anywhere). `|| true` is gone. The line `rc=<n> <last line>` goes to summaries.txt.
2. The gate (Python) demands exactly 9 lines; every line `rc=0`; and the closing text must match `^=*\s*[0-9]+ .*(passed|skipped).* in [0-9.]+s`. Then failed/error must be 0.
3. Floor tightened: pytest's own count from one `pytest --collect-only -q` over the same files; passed + skipped must EQUAL it; skipped <= MAX_SKIPPED=85 (measured 80, margin 5, the 80 itemised in the YAML comment); passed >= MIN_PASSED=970 (measured 988, margin 18). The floor is needed because a conftest that placeholder-skips a file lowers both collected and passed. Measured 988 passed, 80 skipped, 1068 collected.
4. `*_test.py` gap: tracked files under tests/ that match `test*.py` or `*_test.py` but are not in the chunk list fail the job with their names.
Proof, each run as the job's test step under `bash -e` on the no-demo final stack (evidence-nodemo3-6-ci-job-mutants.txt, one process at a time; exit code of the job and its message):
| case | job | message |
|---|---|---|
| baseline | green | TOTAL passed 988, skipped 80, collected 1068 |
| os._exit(0) in the LAST chunk (rv18 green case) | RED | chunk 8: pytest did not finish, last line '....ssssss' |
| os._exit(0) in chunk 0 | RED | chunk 0: pytest did not finish |
| pytest.exit('stop', returncode=0) last chunk | RED | chunk 8: ... last line '!!!! _pytest.outcomes.Exit: stop !!!!' |
| 1 failed test / 1 error (fixture) in last chunk | RED | chunk 8: pytest exit code 1: '1 failed ...' / '... 1 error ...' |
| foo_test.py / testing_extra.py tracked | RED | test files that no chunk would run: ... |
| conftest skips every file | RED | only 0 passed, the floor is 970 |
| last chunk prints 'no tests ran in 0.01s', exit 0 | RED | did not finish |
| ... an empty line, exit 0 | RED | did not finish, last line '' |
| ... '1 error in 0.20s', exit 0 | RED | did not finish |
| ... '1 failed, 5 passed in 0.20s', exit 0 | RED | tests failed in the no-demo copy |
| ... progress line '....s....  [ 40%]', exit 0 | RED | did not finish |
| ... real summary, exit code 1 / 2 | RED | pytest exit code 1 / 2 |
The "ends with ..., exit 0" rows use a test double (shim python, in evidence-nodemo3-drivers/) that runs the chunk's real pytest and then prints that text, because pytest itself cannot be made to print "no tests ran" inside a 10-file chunk. The 10-lines, 8-lines, 0-lines, blank-line, count-mismatch (collected 640/630 vs 639 reported), budget (91 > 90 red, 90 green), and floor (639 < 640 red, 639 green) cases cannot occur through the real loop and are fed to the extracted gate source directly (evidence-nodemo3-5-ci-gate-unit.txt, 25 verdicts, 0 wrong).

## Final stack, evidence
Stack: db54e13 + P1 v3.1 + P2 v2 + P3 v3 + nodemo-fix-v3 + isort + optional-v3 + ci-job-v3.
- No-demo, YAML steps Delete/Ruff/Tests run as-is (evidence-nodemo3-4): ruff clean ("142 files already formatted"), 9 chunks, `TOTAL passed 988, failed 0, error 0, skipped 80, collected 1068`, exit 0. (One pytest at a time, python -u.)
- Demo present, DPLD_REQUIRE_DEMO=1, DPLD_REQUIRE_SCAN=1, gitleaks 8.30.1 (/tmp/work/gl/gitleaks), after `git add -A`: except_hierarchy + hygiene + no_placeholders + gitleaks_exceptions + workflow_files_parse + workflow_run_flags: 218 passed (evidence-nodemo3-3).
- ruff check clean, ruff format --check 151 files clean, mypy --platform linux and win32 "no issues in 28 source files", bandit -ll (src tools scripts, pyproject config) 0 Medium / 0 High, all four workflow files parse (evidence-nodemo3-7).
- Apply matrix (evidence-nodemo3-7): fix-v3, isort, ci-job-v3 apply on db54e13 alone; optional-v3 needs P1 v3.1 first; all 6 orders of P1/P2/P3 followed by the four nodemo patches apply; the nodemo patches in 3 other orders after P1-P3 apply.

## Line for RUN ON LAPTOP (no-demo)
`demo_only/ deleted (git rm), chunked 9 x pytest, python -u, each chunk exit code 0 with pytest's summary line, P1v3.1+P2v2+P3v3+nodemo-fix-v3+optional-v3+isort+ci-job-v3 on db54e13: 0 failed, 988 passed, 80 skipped (1068 collected); ruff check clean (142 files formatted)`. Demo-present side: 218 passed in the 6 affected files; not the full suite with demo present.

## Files
nodemo-fix-v3.patch (+~50 test lines), nodemo-optional-hygiene-repo-v3.patch, nodemo-ruff-isort.patch (unchanged), nodemo-ci-job-v3.patch; evidence-nodemo3-1..8-*.txt; evidence-nodemo3-drivers/ (mut.py, ci_mut.py, run_step.py, gate_unit.py, shim-python.sh).
