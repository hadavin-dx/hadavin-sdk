# PR89 round 9 result review, codebase and test details lens, head ef4c572 (tree 58a9410)

Reviewer: egm codebase-details agent (fresh, read-only, snapshot /tmp/snap/core_P89-ef4c572). Saved by the cloud lead, condensed from the hand-back.
Verdict: 0 Blocker, 0 Major, 7 Minor. Nothing run or hashed by the reviewer. The four pins in the manifest equal the ones in round8-evidence.md (checked by eye); the snapshot files were NOT hashed (two unchanged pinned files are not in the snapshot) and the independent evidence did not exist.
Confirmed (read): all 166 rows "ok" in r8-mut.log; every _WHOLE_ENCODERS entry has a mutant (405 repr, 382 unicode_escape, 383 UTF-8 JSON, 384 bytes, 408 ASCII JSON, 424 ascii); both-quotes branch 423; EXPECTED_MUTANTS 166 true (62 mutant + 104 kmutant); docstring typo at mutation_runner.py:521 fixed; once-only rule enforced by test_g_...occurs_exactly_once.
Not checked: sha256 of any file; whether the full suites truly passed on this head (only summary lines); runner test ordering; tests/test_mutation_runner_helpers.py existence; Windows, network file system, three print layers.

## Minors
1. tests/mutation_runner_mutants.py:30 says "103 mutants there"; real keyword mutants are 104 (the number 102 appears nowhere in the snapshot; if the brief or evidence says 102, that is wrong too).
2. Same docstring lines 32-34 list "the percent-encoded password case (an equivalent mutant...)" under tests with no mutant, but mutants at lines 349, 416, 417 target that case: name the exact test or delete the sentence.
3. Mutant 426 is named "a bare password is not masked in two layers" but removes every layer-0 form with an unescaped double quote for any value; it is killed by the bare test only because that test is more sensitive. Rename: "runner: layer-0 forms with an unescaped double quote are not built".
4. Mutant 407 has the generic expect fragment 'survived the masking': pin the exact assertion text of the guarding test. No mutant for `out.add(encode(form))` (mutation_runner.py:316) or the slice `both[: len(both) - len(suffix)]` (:319); add them (e.g. `len(both) - len(suffix) + 1`).
5. The property tests assert only `MARKER not in masked` (test_mutation_runner_keywords.py:1744, 1761): a mask covering only the marker passes. For second(once) assert out == "E   " + mr.MASK (check it holds for every printer); looser containment only for the `once + "'" + '"'` variant. Fixed seeds 7 and 11: no direct test per encoder entry.
6. The new autouse fixture tests/conftest.py:195-208 (_test_database_address_is_left_as_found) has no test and no mutant: add a test that changes the variable and expects the fixture failure, plus a mutant for `if after != before:`.
7. CHANGELOG line 8 ("Not masked" list) muddles two statements: the libpq backslash-escape sentence is something that IS masked but sits in the "Not masked" list; split it and move it to the "masked" part; the third layer of escaping becomes its own item. CHANGELOG line 12 cites main commit 2a8c2aa and runner sha256 489517fb...: could not be checked.

## Evidence points
- r8-full312.log: "10160 passed, 455 skipped" with NO Postgres; the log has no skip reasons (no -rs): rerun with -rs and group the reasons; confirm the manifest test was not skipped. The conftest fixture's real branch (variable set before the test) only runs with a DSN; last DSN runs were at 6706e67. State plainly that gates at ef4c572 are green only for the no-DSN configuration, or run once with a throwaway DSN (the independent runner does this).
