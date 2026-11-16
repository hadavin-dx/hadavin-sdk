# A24 PR91 fix batch 1 builder report (agent a1033ae1f57cff1ac, head 92412fd). Saved by the cloud session from the hand-back.

A24 PR91 round 1 fixes are done in one batch and pushed to origin core/ci-scan-config-guard-fix1. Head SHA is 92412fd531565a61db8979d2485c499d6fdc994d. Branch was cut from 61cf2be. I did not run the checks CodeQL, SonarCloud and CodeRabbit.

Not checked, or weaker than you may assume:
- The reviewer's Blocker B1 was real. I ran 61cf2be's own scan on a clean export and it exits 1 with 6 hits in tests/test_ci_toolpath_step.py (log: .../scratchpad/old-real-scan.log).
- Fail-before proof is partial. Against the old tools/scan_repo.py, 51 of 116 tests in tests/test_scan_repo.py fail (log: .../scratchpad/old-head-scan.log). These include the new widened-marker, replaced-marker, NUL, glob, new-marker-shape, pinned-list-file and print-list tests. Some of those failures are only because the old code cannot read the new list format. test_a_marker_moved_to_another_line_with_identical_text_still_passes fails on old code only for that reason. test_a_weakened_copy_of_the_real_list_fails_the_scan (N5) passes on old code by design.
- For G5 I did not run the new pyproject tests on old code. Instead I showed the old check accepts 5 top-level [tool.ruff] keys (extend-ignore, exclude, extend-exclude, select, extend-per-file-ignores); the new check rejects them (log: old-pyproject-check.log).
- Bandit: `bandit` is not on the test group, so I ran it as `uv run --only-group scan bandit -q -r src demos tools -ll`, exit 0.
- N3 is only partly done. I added the header note and regenerated the baseline entries, but I did not write the ledger rows "baseline, review pass planned", because handover/ledger.md is outside this worktree. The lead should add them.
- M1: I added .github/CODEOWNERS. The owner handle in it, @veerarakesh56, is a guess taken from the git author noreply address. Please check it before merge. The ruleset that enforces CODEOWNERS is owner-only and not done. The list header and CODEOWNERS say the guard is a review aid until the ruleset exists.
- N2: the frozen-old-step test skips only when commit 2742c1b is not in the clone (a shallow checkout).
- The ci.yml comment (N1) is a comment-only edit.

Gate, run on the final head. The three affected test files give 312 passed (log: .../scratchpad/new-head.log). The full suite via heavy.sh with `-m "not live and not perf"` gives 10174 passed, 454 skipped, 28 deselected (log: .../scratchpad/full.log).

| Check | Result |
|---|---|
| ruff check | exit 0 |
| ruff format --check | exit 0 |
| bandit -ll | exit 0 |
| python tools/scan_repo.py | exit 0 |

Per group:
- **G2 (M2):** a marker's list value is now `count@sha256`, where the hash covers the sorted marker line texts. A widened or replaced marker fails with "text hash differs". The same text moved to another line still passes; this is documented in a test. I added `python tools/scan_repo.py --print-list`, which writes the list and keeps existing reasons. All entries were regenerated with it, none by hand.
- **G3 (M3):** the config-name and hash checks and the marker check now run before the NUL skip. A tracked file with a source or config extension that contains NUL is a hit (`nul-in-text-file`).
- **G4 (M4):** `ruff: noqa`, `flake8: noqa` and bare `nosem` are now markers. This found 3 real file-level `ruff: noqa` suppressions that were invisible before: tests/demo_askdata/corpus.py, fuzzgen.py and test_validate_harm.py. They are now listed with a reviewed reason and need your review.
- **G5 (M5):** added ruff.toml, .ruff.toml, trivy-secret.yaml, bandit.yaml, bandit.yml, setup.cfg and tox.ini to the scanner config names. The whole [tool.ruff] table is pinned in tests/test_ci_gitleaks_scope.py through the constants RUFF_PINNED, RUFF_LINT_PINNED and RUFF_SWITCH_KEYS. There are negative tests for each switch key at the top level and under lint, and one for a changed pinned value.
- **G6 (M6):** an allowlist path containing `*`, `?` or `[` is refused. tools/scan_allowlist.txt and tools/scan_banned_extra.txt are hash-pinned like scanner configs.
- **G1 (B1):** six markers in tests/test_ci_toolpath_step.py were reduced to one `_run` helper with a single noqa S603, and it is listed with a reviewed reason. I also switched git calls to an absolute path, which removes the S607 markers. The list was regenerated last.
- **G7:** N1 comment added in ci.yml. N2 stays frozen, labelled with commit 2742c1b plus a git-history equality test. N3 as above. N5 test added.

Files changed:
- tools/scan_repo.py
- tools/scan_suppressions.txt
- tests/test_scan_repo.py
- tests/test_ci_gitleaks_scope.py
- tests/test_ci_toolpath_step.py
- .github/workflows/ci.yml
- .github/CODEOWNERS (new)

Raw logs are in /tmp/claude-0/-home-user/39edf7c7-26f2-5129-9a6e-500351b26399/scratchpad/.

Cleanup: no background processes of mine remain, and I did not touch other PR branches or repository settings. Not run, because there is no CI here: CodeQL, SonarCloud and CodeRabbit (see top). A fresh review pass is still required after this batch because the path is uncapped.