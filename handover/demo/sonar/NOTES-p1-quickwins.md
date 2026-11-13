# P1 quick wins: NOTES (base db54e13, patch sonar-p1-quickwins.patch)

Rules used: the preamble's R-numbers could not be looked up (no bible folder in this shell); I applied preamble points 5, 6, 7 and 20 (fix, honesty, class-level fix, code-last). EGM (preamble 13) was NOT run by me: the lead runs it.

## What did not work or is uncertain (first)
- I cannot see the SonarCloud result. Everything under "expected to clear" is a prediction.
- The rule text for githubactions:S6506, S8541 and shell:S7688 was not returned by the SonarCloud rules API in this shell (empty description), so the exact accepted spelling comes from the issue message plus the published flag meanings. S8541 message says `--only-binary :all:`; I used exactly that spelling. sonar.yml already uses `--only-binary=:all:` and was NOT flagged, so I left it.
- The venv here is Python 3.13; CI uses 3.12. `pip install --require-hashes --only-binary :all: -r requirements-dev.txt` succeeded here (so every pinned package has a wheel for 3.13/linux); not run on 3.12, not run on the real runner.
- Not run: the full test suite (lead does), 8 playwright tests (module not installed), 3 gitleaks tests (no gitleaks program on PATH; I only downloaded and checksum-checked the pinned archive, which proves the new curl flags work), Windows, CodeQL.
- The raw invisible (non-direction) characters U+200B, U+2028, U+2029, U+FEFF on the same test lines are still raw in the file; Sonar did not flag them and the new hygiene test covers direction controls only.

## Changes
| file | change |
|---|---|
| .github/workflows/lint.yml | curl gets `--proto '=https' --proto-redir '=https' --tlsv1.2` (checksum check kept); pip install gets `--only-binary :all:` and is a `run: |` block (a plain scalar would hold ": " and break YAML, the exact earlier sonar.yml bug) |
| scripts/reset.sh, scripts/start_all.sh | every `[ ]` test is `[[ ]]` (shebang already `#!/usr/bin/env bash`; `=` became `==` in one test) |
| tests/test_followup_edge_cases.py | the two raw U+202E characters are now the escape `‮` (same string value) |
| tests/test_smtp_provider.py | the self-comparison is now: a second outbox object gives the same recipient for 40 keys |
| tests/test_lead_step_route.py | one string assertion on start_all.sh updated to the `[[` spelling |
| tests/test_hygiene.py | new: no tracked file holds a raw direction control (+ a test the pattern sees all 12 characters); no single-bracket test in tracked .sh and each starts with the bash shebang |
| tests/test_workflow_files_parse.py | new: every curl in every workflow has the 3 flags; every pip install has `--only-binary[ =]:all:` and `--require-hashes` |
| tests/test_reset_scripts.py | new: start_all.sh refuses an unknown mode (exit 1, nothing created), a run of the changed [[ test |

## Per-rule count (issues in issues-pr4-0253.json fixed here)
githubactions:S6506 1, githubactions:S8541 1, shell:S7688 10 (reset.sh 6, start_all.sh 4), text:S6389 2, python:S5863 1 = 15.
Siblings checked: other workflows (codeql.yml, sonar.yml) have no curl and sonar.yml's pip line already has the flag; only two tracked .sh files; raw direction characters exist in no other tracked file (scan of git ls-files); no Dockerfile/Makefile.

## Rung table (preamble 20)
| component | need | rung tried | verdict |
|---|---|---|---|
| download flags, pip flag, `[[` | quiet 15 findings | standard tool options (curl, pip, bash) | CUT-TO-CONFIG, no new code |
| the 4 new tests | stop the findings coming back | existing test files extended; no new tool | KEEP (small, static) |

## Rungs: run / not run
| what | result | file |
|---|---|---|
| 7 affected test files after the patch | 234 passed, 11 skipped | evidence-p1-1 |
| new tests against OLD code | 4 failed (curl, pip, bidi, single bracket) | evidence-p1-2 |
| ruff check, ruff format --check, mypy linux and win32, bandit -ll | all clean | evidence-p1-3 |
| SMTP: mutant (recipient depends on object id) | new test FAILS, old line PASSES, real code passes | evidence-p1-4 |
| actionlint v1.7.7 (not pinned in repo; archive checksum from the same release page) on 3 workflows | no findings | evidence-p1-5 |
| real download with the new curl flags + checksum | OK | evidence-p1-6 |
| git apply --check on fresh db54e13 | OK | evidence-p1-7 |
| playwright, gitleaks tests, full suite, Windows, real CI | NOT run | |

S5863 and S6389: no behaviour changed, so a "fails before" exists only for the hygiene test (2 hits on old code) and the SMTP mutant above.

## Series overlap
Touches lint.yml, scripts/*.sh and 5 test files. db54e13 already contains the sonar.yml fix and tests/test_workflow_files_parse.py (the v2 lead patch no longer applies to it); this patch only appends to that test file. Expected conflicts with P2/P3: only if they edit the same test files (test_hygiene.py, test_smtp_provider.py are appended/edited at distinct places); not tested against P2/P3.

## Expected to clear on SonarCloud
S6506 (flags present on the only curl), S8541 (flag in the spelling of the message), S7688 x10 (no `[ ` left), S6389 x2 (no raw bidi char left in the file), S5863 (two different expressions). Risk: S7688 may also want `[[` inside `case`/other forms (none exist), and S6506 may want `--tlsv1.3` or only `--proto` (unknown; rule text unavailable).
