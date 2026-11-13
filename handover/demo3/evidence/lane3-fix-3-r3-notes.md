# lane3-fix-3 round 3 (tests only, file tests/test_path_confinement_lane3.py, base f3c39cf8)
Patch: lane3-fix-3-r3.patch, sha256 b272b9a88b6daa96dc76cc7ed150552c1d16ee26b8aee051ed374db88db4d4ed
| finding | change | proof |
|---|---|---|
| 1 name limit | now tests pc._new_name directly: MAX-1 and MAX accepted, MAX+1 refused; "é"*MAX passes the length check and is stopped by the character table (a byte-count mutant would fail); no file system | M20 fails the new file |
| 2 docstring | lists M03, M08, M11, M15, M20, B1, B2; says B1 and B2 are the author's extra mutants, not in the Q8 log | read |
| 3 second route | docstring says the patched-commonpath test is a second route; main proof is the mock-free input | read |
| 4 skips | sys.platform == "win32" (import sys added), same meaning | skips unchanged |
Neighbour (a) _roots realpath->abspath: the OLD test tests/test_path_confinement.py::test_explicit_roots_are_resolved_so_a_link_as_a_root_works fails on it, so nothing added. (b) normcase: not added (Windows-only).
Counts unmutated: new file alone 15 passed, 1 skipped; with tests/test_path_confinement.py 393 passed, 2 skipped (same as round 2).
Mutants M03, M08, M11, M15, M20, B1, B2 each FAIL the new file alone (first failing test per mutant in the run log); each restored; git status shows only the test file. M11/M15/M20 etc. were re-made by me as one-line edits (the Q8 mutant files were not scripted).
git apply --check: fresh f3c39cf8, after claims stack, after claims + lane3-fix-1: all ok.
