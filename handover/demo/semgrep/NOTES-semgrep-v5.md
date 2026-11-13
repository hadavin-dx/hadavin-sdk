# NOTES semgrep-on-db54e13-v5.patch (builder, UNREVIEWED by a fresh reviewer)

sha256 99c185b0298fa8a9e4798bf571ab72c3c27cfd0a7a1094efbd7c3fc62622b7c5  semgrep/semgrep-on-db54e13-v5.patch (9 files, same as v4)

## What failed / what I did not run (first)
- NOT run: Semgrep with the p/python and p/javascript rules. They come from the registry, are not available offline, and I did not fetch them. semgrep 1.185.0 itself is installed (hash-locked install from this repo's lock, venv /tmp/work/sg2-venv-sg; `semgrep --version` prints 1.185.0). No GitHub run seen.
- NOT run: the full pytest suite (the lead runs it), actionlint (not installed), the docker lock command.
- The old v4 on db54e13 + P1 v3.2 FAILS P1's test: confirmed (evidence-sg5-3): 1 failed, 106 passed; flagged semgrep.yml#block-3 lines 7, 9, 11, 13.
- gitleaks `dir` on the working tree reported 25 hits, all inside git-ignored caches (__pycache__, .mypy_cache, .ruff_cache) created by my test runs; a clean clone of the committed tree: no leaks (evidence-sg5-2).

## What changed v4 -> v5 (measured by diffing the added/removed lines per file)
7 of 9 files identical (.codeant/configuration.json, .gitleaks.toml, exceptions.txt, requirements-semgrep.in, requirements-semgrep.txt [sha256 a791abb7e447..., 1130 lines, 919 --hash lines], both new tests). v4 applies unchanged on db54e13 (`git apply --check` OK); only the two edits below were made:
1. .github/workflows/semgrep.yml: the 4 `[ ... ]` in the scan step run block are now `[[ ... ]]` (`-ne 2`, `-lt 3`, `-eq 1`, `-ne 0`; all are integer tests, the same in `[[ ]]`). Nothing else in the step changed.
2. Stale wording, fixed factually (docs/tests.md "Status of the scan" and the semgrep.yml "Status:" comment): "ERROR-level clean on the stack head at 0841f36" -> "on commit 0841f36 of the branch pr-3-tests" ("stack head" meant the tip of a branch stack that no longer exists). The workflow comment adds "(an earlier commit; the scan was not repeated on later ones)". docs/tests.md adds: "The scan was not repeated on later commits of the branch: 13 files in the five scanned folders changed between 0841f36 and db54e13 (405 lines added, 60 removed)" (I measured it: `git diff --shortstat 0841f36 db54e13 -- src scripts load_tools tools n8n`; 0841f36 is an ancestor of db54e13; 2db3926..db54e13 changes nothing in those folders).
No comment in sonar.yml or lint.yml mentions 2db3926 or "stack head" (grep over the whole tree: only the two places above, plus unrelated history lines in docs/tests.md, 2ce1f98/0841f36 as measurement commits, which stay true).

## Is `shell: bash` needed? No, not added.
- GitHub runs a `run:` step with no `shell:` on Linux as `bash -e {0}`; an explicit `shell: bash` runs `bash --noprofile --norc -eo pipefail {0}`. The only difference is `pipefail`, and the scan block has no pipe. I did not add it: it would change the runner command line for no gain. P1's test (`_workflow_shell_problems`) passes when the key is absent or `bash`, fails for any other shell, at step and job-default level; semgrep.yml has no `shell:` key and no `defaults:`.
- Proof the behaviour is unchanged (evidence-sg5-5): the run block was extracted from the old and new YAML and run under bash with a stub `semgrep` giving exit 0, 1, 2, 3, 7 and "2 then 0": the exit status, the number of tries and the printed messages are identical in all 6 cases, under both `bash -e` and the explicit `bash --noprofile --norc -eo pipefail` form. (Stub test of the shell logic only, not of Semgrep.)
- PyYAML parses the new semgrep.yml (jobs: semgrep; no shell keys).

## Rung table (what was run)
| step | result |
|---|---|
| git apply --check on clean db54e13, v5 alone | OK |
| apply matrix (evidence-sg5 matrix in this file's section below): v5 alone; v5 with each of P1 v3.2, sonar-yaml-test-trimmed-v2, crlf-guard-v5, P2 v2.1, P3 v3, nodemo-fix-v2 in both orders; 6 full orders of all 7 | 19 of 19 OK |
| tests on v5 alone (git add -A; gitleaks 8.30.1, DPLD_REQUIRE_SCAN=1) | test_nosemgrep_form 63, lock 3, exceptions 44, workflow_files_parse 5, hygiene 15: all passed |
| ruff check / format --check / mypy linux / win32 / bandit -ll (v5 alone) | all clean (exit 0) |
| combined tree, all 7 patches | mypy linux+win32 clean (28 files), ruff clean, bandit exit 0; test_shell_single_bracket 107 passed, workflow_files_parse 12, nosemgrep_form 63, lock 3, exceptions 44, hygiene 24: all passed |
| gitleaks dir / git | clean clone: no leaks; git: 24 commits no leaks |
| semgrep rules (registry) | NOT run |

## Apply matrix (raw: /tmp/work/sg5-matrix.txt, copied below)
# apply matrix on clean db54e13 (git apply --check each step, then apply)
OK    sg
OK    sg p1
OK    p1 sg
OK    sg yaml
OK    yaml sg
OK    sg crlf
OK    crlf sg
OK    sg p2
OK    p2 sg
OK    sg p3
OK    p3 sg
OK    sg nd
OK    nd sg
OK    p1 yaml crlf p2 p3 nd sg
OK    sg nd p3 p2 crlf yaml p1
OK    p1 sg yaml crlf p2 p3 nd
OK    nd p3 p2 crlf yaml p1 sg
OK    yaml p1 sg crlf nd p2 p3
OK    p3 nd sg p1 p2 yaml crlf

## Wording for the lead's PR body (semgrep-pr-body-v5.md), not edited by me
- "`2db3926` is the commit this PR is cut from" -> `db54e13` (branch pr-3-tests head, which already holds the sonar.yml fix and tests/test_workflow_files_parse.py); "based on the branch that holds the earlier pull requests #2 to #4" still fits.
- "The diff of this PR is the patch with sha256 60e36273..." -> 99c185b0298f...
- "This PR is cut from a later commit ... 2db3926. Since 0841f36, 13 files ... (405 added, 60 removed). The scan was not repeated on 2db3926" -> same numbers hold for db54e13 (measured); say db54e13.
- Add: the scan step uses `[[ ]]` tests (shell rule S7688); no behaviour change.
- "ERROR-level clean on the stack head at 0841f36" -> "on commit 0841f36 of the branch pr-3-tests".
Evidence files: evidence-sg5-1..7 in this folder.
