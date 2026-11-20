# TIDYT build notes (G10/M3 tidy, textnorm lane), branch wip-tidyt

Base: cloud/core-c HEAD ca469a0bf. Commits: "code G: tidy ..." (src, tests) then "notes: ..." (CHANGELOG, manifest, these notes).
The manifest hash test (tests/test_textnorm.py) and meta test i (CHANGELOG mutant sentence) are RED on the code commit alone and green with the notes commit.

## Changes
- M3 N1: `textnorm._deadline_of` catches `OverflowError` from `math.isfinite` (an int such as 10**400) and raises `NotText`. Test: 10**400 and its negative join the D-7 bad list. Mutant "deadline: a huge int budget raises OverflowError"; "a bad budget is no budget" re-pointed (same mutation: the whole check gone).
- M3 N3/N4: `test_a_wall_factor_of_exactly_one_is_accepted` (int 1 and 1.0, both deadlines) with mutants `1 <=` -> `1 <` in textnorm and injection; `test_the_seconds_left_are_the_smaller_of_the_cpu_left_and_the_wall_left_over_the_factor` (budget 30, CPU 10 and wall 40 spent: CPU left 20, wall left 20, budget_s 10; and the CPU-cap side) with mutants "not divided by the factor" and "the larger of the two".
- M3 N5: `scan_holds` docstring: the wall rule (`injection._left`). N6: the 8 names (FILLERS, key_tag, FOLD_VERSION, squeeze, AllowVerdict, fold_views, squeeze_views, scan_keyset) named as internal helpers (no caller in another src module, decided by grep and AST). N7: CHANGELOG M3 item says "four" stale sentences (it listed four).
- G10 r2 N3: `NotText` docstring covers a bad budget. N4: D-8 / D-8b docstrings reworded (D-8b: injection_check, AnyOf, combine). Mutant list header: groups add up, 77 + 26 + 14 + 5 + 31 + 10 + 77 + 28 = 268.
- Not done: M3 N2, N8 (no change wanted); G10 r2 N1/N2/N5 not in this task.

## Counts
- Mutants 263 -> 268 (256 behaviour, 12 wording). Deadline tests 17 -> 19. Public names 37 unchanged.
- sha256 of guard/textnorm.py: `928a4247fa0eb1a67a7e32c6a2fb644f2c3fb7beaec2dd7b3f09d8c97c036945` (manifest and CHANGELOG).
