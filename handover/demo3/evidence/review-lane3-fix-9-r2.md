# Fresh review of lane3-fix-9-r2.patch (sha256 b1215b5a...), reviewer egm:egm-codebase-details, read-only, no commands run; saved by the lane 04:09Z
Result: 0 blocker, 0 major, 4 minor.
Spec items 1-4 PASS by reading (helper used by all 3 old blocks; conftest hook correct for pytest incl. symlink and fail-safe default; returncode assert before "passed"; _copy_repo fails loudly without git). Item 5 (helper identical to core): not judged by reviewer.
New tests fail on old code: probe test shown failing in raw/b11-fails-before.log; the copy test by reading; helper unit tests fail only by import error (not a behaviour proof).
Minors:
1. tests/conftest.py:48 overwrites any exit status with TESTS_FAILED (would replace INTERNAL_ERROR 3, USAGE_ERROR 4, INTERRUPTED 2 by 1). Set only when status is OK or NO_TESTS_COLLECTED.
2. support.py helper has a check-then-act race under parallel workers and follows a `data` symlink (strict xfail documents the symlink); xfail reason text names "core r7f" (internal label in a public repo: wording rule). Neither triggers today (no xdist).
3. Two added `# noqa: S603` in test_data_folder_helper.py (suppressions): rewrite or accept explicitly.
4. tests/test_mode_safety.py ~297: ruff-format split `with book_folder_in_repo(\n "reset-no-ps-"\n) as folder:  # comment`; move the comment above.
Could not check by reviewer: any run, 3722-pass claim, helper == core, Windows, -p no:terminal, xdist.
