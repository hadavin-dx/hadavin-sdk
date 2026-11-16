# P2d-1 evidence (head 6d5616bf50be0c544e03ba399aa720bfe6224bb2, branch core/P2d-1)

## Failures, slips and what was NOT run (first)
- None of the full runs failed (3.12 and 3.13: 10172 passed each).
- Slips: my first mutants file had 9 bad rows (6 wrong `expect` text, 1 indentation error in the N1 mutant, 1 killed by a different test than the pinned one, 1 survivor). Fixed; the final run is 42 of 42 good. No mutant was declared equivalent in the file. REG-M of the ticket IS equivalent (see BN.md) and was replaced.
- The first 3.13 full run used `-x` and never gave a summary line; it is not counted. Rerun below without `-x`.
- Not run: any live model call. CI itself (not run locally). `tools/` bandit was run only after the first handback.
- The DM spy counts "256" and "301" are numbers from test comments for the mutants DM-1 and DM-1b. They were not measured as mutant counts; the mutation run only shows the tests fail on those mutants. What I measured: on the real code with a clock that never trips, 256 stored originals are unpacked before the cap of 256 refuses the text; this is not a measure of the guard. The guard itself is the test HOSTILE-2 (at most 1 call), which passes.
- The 18 fail-before passes are labelled "pin" or "other" by test NAME only, not by deeper analysis.

## Environment
- Python 3.12.13 (py3.12 run, default venv of the build dir) and 3.13 with own UV_PROJECT_ENVIRONMENT=<build-dir>/venv313 style path (<tmp-dir>; import path is the package under the P2d-1 worktree via the editable install).
- Heavy jobs went through heavy.sh (3 machine-wide slots). Load average seen: 4.6 (13:00), 4.1 (13:32). Max parallel jobs of mine: 2 (the two full suites).

## Ruff, format, bandit
- `ruff check src tests demos`: All checks passed.
- `ruff format --check`: 326 files already formatted.
- `uvx bandit -q -r src demos tools -ll`: warnings only (nosec / test-name comments), no findings. (bandit is not in the test group, so uvx; version not pinned to the CI's 1.9.4.)

## Fail-before
Method: throwaway worktree of the head with redact.py, runmap.py, defaults.py restored from c5d16e0 (P1a already merged in both). Command: pytest on test_redact_fold*.py + test_k5_round12_fuzz.py with `-m "not perf"`.
Result: 65 failed, 18 passed, 6 xfailed, 2 errors, 3 deselected in 36 s (raw: failbefore-raw.txt).
- The 2 errors (test_err_1, test_seam_2 in test_redact_fold_seams.py): both are SETUP errors of the autouse fixture `clean_char_cache`, which calls `redact_mod._char_class.cache_clear()`; the old module has no `_char_class` (AttributeError). So they fail before for a missing feature, not on their assertion. The two other seams tests (SURR-1, SEAM-3) fail on their assertions.
- The 18 passes on the old code (by name): pin = holds before and after by design; other = not a pin.
  - pin: leaves_an_existing_placeholder_alone, native_digits, in_place_masking_cases x3 (zero-width, nbsp, cookie), pem_1, map_3, variant_1_b, view_2, budget_1, dm_2 (257 refuses / 256 passes, same before), and the 5 test_k5_round12_fuzz tests (existing guards).
  - other: withhold_rate_is_measured_and_pinned (a rate measured on both trees), ctrl_1 (a control for the outcome helper).
- 6 xfailed on the old code: GAP-1, VARIANT-1(a), VARIANT-1(c), P1B-1 x3.

## Targeted tests on the new code
`pytest` on test_lockin_guard, test_no_hardcoded_values, test_no_reference_material, test_repo_rules, test_redact_fold, _seams, _property, test_k5_round12_fuzz: 182 passed, 4 xfailed in 34.66 s (4 xfailed: GAP-1, VARIANT-1(a), VARIANT-1(c), RESTORE-1).
Perf alone (`-m perf`, budget file): 3 passed in 35.72 s; test_hostile_1 18.91 s; test_align_1 11.12 s; the 130k-lines test 5.59 s.

## Mutation run
`<build-dir> uv run --all-extras --group test python tests/redact_mutants.py`: "42 of 42 good; problems: []" (mutation-raw.txt has every row). 21 ported from PR 50, 21 new (N1, N4..N12, N14, N15, R1..R3, DM-1, DM-1b, REG-M (replaced: the rollback keeps the counters), REG-M2, AL-1, AL-3). R1 and mutant 17 are allowed to crash with AssertionError and are reported KILLED.

## Measurements
- Alias fold of 5,000 values: 0.173 s CPU.
- ASCII-4 shape at N=1000 stored non-ASCII values: 1 build, 1000 folds of the stored values, 0.095 s CPU (py3.12).
- Code points whose fold is longer than their NFKD: 71.
- sha256 of src/hadavin_sdk/guard/redact.py: ef330f6b5ddb20aef88d44504d69f102d9a9eb90018d8ee76fd7e0b52a9ab09d.

## py3.12 full
`heavy.sh uv run --python 3.12 --all-extras --group test pytest -q -p no:cacheprovider` at 6d5616b: 10172 passed, 455 skipped, 9 xfailed in 590.49 s.

## py3.13 full
`UV_PROJECT_ENVIRONMENT=<tmp-dir> <build-dir> uv run --python 3.13 --all-extras --group test pytest -q -p no:cacheprovider` (no `-x`) at 6d5616b: 10172 passed, 455 skipped, 9 xfailed in 423.21 s; 0 FAILED/ERROR lines.
