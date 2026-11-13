# rv5 review: crlf-guard-v3 and sonar-yaml-fix-v2

Reviewer: fresh independent, shell. Scratch: /tmp/work/rv5-508 (trees, venv, scripts in /tmp/work/rv5-scripts). No pushes, no network writes (one read-only download of gitleaks 8.30.1 to run the real scan). Made-up data only.
Bible/RULES.md and handoff files are NOT on this machine, so no R-numbers could be cited (preamble rule 1 not satisfiable here). EGM skills not run: this is the independent review step only (rule 13).
Tools: ruff 0.17.4, mypy 2.4.1, bandit 1.9.4, pytest 9.2.0 from requirements-dev.txt (hash-checked); uv --group test does not exist in this repo (no dependency groups in pyproject), so a venv was used.

## FAILURES (lead with these)

### F1 (Major) crlf-guard-v3: the lead's rule "every mutant must die" is NOT met. 8 of my 19 new mutants survive, plus the builder's own M3b.
My mutants (tests/test_hygiene.py, 20 passed + 3 skipped without gitleaks; same result as clean tree):
- SURVIVED N15: the sed cure in CRLF_HINT changed from `s/\r$//` to `s/x//`. The message text (the thing the lead wants tested end to end) is only checked for the substring `sed -i`, never the command itself.
- SURVIVED N17 (scan call `--exit-code 1` -> 0) and N18 (scan call without the report format, so no file name in the message): these edit the real gitleaks call in test_hygiene_scan_public. Same family as the builder's M3b. They need gitleaks AND a planted CR tree; no automatic test does that. (I ran the real path by hand: see "Real gitleaks check" below, it works; it is just not a test.)
- SURVIVED N4: LF_ONLY_FILES cut to only sonar-project.properties (the comment promises .gitleaks.toml, exceptions.txt, patterns.txt, requirements-*.txt). Only one of the five entries is exercised.
- SURVIVED N7 (_flagged_files: bad JSON now raises instead of returning []), N9 (message drops "values are redacted"), N11 (non-empty-list safety assert removed), N13 (.ps1 exemption case-sensitive: `RESET.PS1`).
- KILLED (11): N1 hint loses git checkout; N2 ps1 not exempt; N3 extra exempt kind; N5 note always empty; N6 ./ prefix kept; N8 file list dropped; N10 filter off; N12 missing file not skipped; N14 guard message loses cure; N16 every file reported; N19 wrong git cwd.
Note: N9, N11, N13 are low value; N15, N17/N18 (and M3b), N4 are the ones that matter.
Fix: add one test that takes the cure command out of the message and EXECUTES it on a planted file, then asserts the guard passes (this also closes F2); add a planted-CR-tree test run under gitleaks when present (skipped otherwise) asserting the file name and hint appear in the real failure; parametrize the guard test over every LF_ONLY_FILES glob.

### F2 (Major) crlf-guard-v3: the cure in the message does not cure the lone-CR case the patch itself tests.
`sed -i 's/\r$//'` on a lone-CR file (`a=1\rb=2\rc=3\r`) leaves `a=1\rb=2\rc=3` (checked with GNU sed here): only the final CR goes, the guard still fails. The v3 tests plant a lone-CR file (`lone-cr` params) and assert only that the text contains `sed -i`; they never run the advice. `git checkout -- <file>` is correct for both. Fix: say `git checkout -- <file>` first, and give a cure that works for lone CR (`tr '\r' '\n' < f > f.new && mv f.new f` for lone-CR, `tr -d '\r'` for CRLF), or drop lone-CR from the claim.

### F3 (Minor) the sed cure is GNU-only. The people who get CRLF files are on Windows (Git Bash has GNU sed; PowerShell/cmd do not) and macOS BSD sed needs `-i ''`. State that or give a portable line (`git checkout -- <file>` or an editor setting). Real Windows still not tested (builder says so).

### F4 (Major, apply) sonar-yaml-fix-v2 does NOT apply on current head db54e13.
db54e13 already contains the v1 of this fix. See apply matrix. Both hunks fail: sonar.yml hunk (already applied) and `tests/test_workflow_files_parse.py: already exists in working directory`. Since the sonar.yml in v2-applied-to-2db3926 is byte-identical to db54e13's, only the test file differs. I built the delta: /tmp/work/rv5-508/delta-v2-on-db54e13.patch (138 lines; `git apply --check` OK on db54e13; 11 tests pass after it). The lead should ship that delta, or v2 only for base 2db3926.

### F5 (Minor) sonar-yaml-fix-v2: 5 of my 27 mutants survive (and 1 more by design).
Real sonar.yml mutants (13): 12 killed; SURVIVED R8 (`timeout-minutes` -> `timeout-minute` at JOB level: only step keys are checked, job keys are not; by design, actionlint's job).
Test-code mutants (14): 9 killed. SURVIVED T7 (no-jobs branch removed), T8 (top-level-not-mapping branch removed), T12 (empty-steps branch removed), T14 (step-not-a-mapping branch removed): `problems()` has these four branches but the 6 in-memory cases do not reach them. T10 (a YAML error no longer fails the test) and T13 (the final assert neutered) survive only because all real files are good; they are caught only through the real-file mutants R5/R12, which are on the real file, i.e. fine as a pair. Fix for T7/T8/T12/T14: four one-line parametrized cases (`jobs:` empty, list at top, `steps: []`, `- just a string`) OR delete the four unreachable branches (smaller, and the lead wants it small).

## Verdict
- crlf-guard-v3: NOT merge-ready by the lead's rule (F1, F2). The mechanism works (real gitleaks check below) but the message content is not verified by running it, and one cure is wrong.
- sonar-yaml-fix-v2: logic and size acceptable; apply on db54e13 needs the delta (F4); small survivor list (F5).

## What passed
### Apply matrix (git apply --3way; C=crlf-guard-v3, S=sonar-yaml-fix-v2, V=versions-md-allowance, G=semgrep-on-2db3926-v4)
Base 2db3926: each patch alone OK; all 8 orders I tried (CSVG CSGV CGSV SCVG GCSV VGSC GVCS SGCV) apply all four cleanly. C and G both edit docs/tests.md: no conflict in any order.
Base db54e13: C alone OK, G alone OK; S FAILS (F4); V FAILS as a forward apply because db54e13 (commit 7a386bc) already contains it (it reverse-applies cleanly, so it is fully contained). In all 8 orders: C, G, V ok (V as no-op under 3way), S fails.
Overlap answer: db54e13 = 2db3926 + 7a386bc (versions.md allowance == versions-md-allowance.patch) + the v1 sonar.yml block-scalar fix and a 38-line test_workflow_files_parse.py. It does contain the sonar.yml fix. `git diff 2db3926 db54e13`: only sonar.yml, tests/test_workflow_files_parse.py, versions.md. (Remote main is a0b97a4 and does not contain either commit; db54e13 lives on origin/pr-3-tests.)
### Gates (trees: C only, S only, all four patches)
ruff check: all passed (3/3). ruff format --check: clean (3/3). mypy --platform linux and win32: success 26 files (3/3 each). bandit -ll: exit 0. 
### Tests
- C: tests/test_hygiene.py 20 passed, 3 skipped (no gitleaks); with gitleaks 8.30.1 (GITLEAKS_BIN) hygiene scan and canary tests pass.
- S: tests/test_workflow_files_parse.py 11 passed; base db54e13 v1 4 tests.
- All four patches, touched files + test_nosemgrep_form, test_gitleaks_semgrep_lock, test_gitleaks_exceptions, with gitleaks: 145 passed.
- Full suite on all-four tree: first run with -x stopped at the flaky failure below after 1114 passed, 29 skipped (389 s); a second full run hit my 590 s timeout with no result, so a COMPLETE full-suite pass was NOT obtained. Touched files and the 145-test subset above did pass.
### Real gitleaks check (manual, 8.30.1): planted CRLF into sonar-project.properties of a copy; test_hygiene_scan_public fails with `gitleaks dir reported findings (values are redacted); files: ['sonar-project.properties']` + the CRLF hint; test_the_secret_scan_files_have_no_carriage_return fails with the hint. The message path works for real CRLF.
### sonar-yaml-fix-v2 size/scope against the lead's order
Present: runs-on (or uses), steps with known keys (the 11 GitHub step keys, complete), top-level `on` (True accepted), docstring says what the test cannot see and that actionlint finds it. 130 lines, 6 test functions, 11 cases, no YAML-linter machinery, no new dependency. Nit: slightly beyond the order (exactly-one-of run/uses, job-uses short-circuit, jobs/steps non-empty); and the docstring says actionlint "is not run by this test ... add it as a separate CI step" rather than stating it is the real control; actionlint is not wired in CI here (only a .coderabbit.yaml mention). Nit: PyYAML is not in requirements-dev.in, it is in the lock only through bandit; fine today, same as v1. Nit: glob is `*.yml` only, a workflow named `.yaml` is not checked.
### Other Nits
- N: crlf `.editorconfig` has `[*] end_of_line = lf`, which also covers binary files (icon.png); harmless.
- N: first full-suite run (with my mutant runs going in parallel) had one failure, tests/test_later_approval.py::test_resolve_413_drains_the_unread_body_like_post_leads; passes alone (29 passed) on the patched tree AND on pristine 2db3926: timing flake under load, not from these patches.

## Not checked
Real Windows; macOS; `git`-mode gitleaks history scan (DPLD_REQUIRE_SCAN=1); CI behaviour of Sonar/CodeQL; actionlint (not installed); EGM skills; bible R-numbers; token use not measured.
Files: /tmp/work/rv5-report.md, /tmp/work/rv5-508/delta-v2-on-db54e13.patch, /tmp/work/rv5-scripts/{mut.py,crlf.json,sonar_real.json,sonar_test.json}. Head SHAs tested: 2db3926, db54e13.
