# C9 results (base 61ded9e + patches + survivor-tests-v1; copy at RR/tmp-C9/work; tree-C9 untouched)
Nothing failed in the runs below except the expected mutant failures and the v1 -OO failure (reported first).
Not run: Windows, full suite, any file other than the two survivor files + test_take_script_refusals.py.

| run | what | passed | failed | skipped | wall | hang |
|---|---|---|---|---|---|---|
| 01 | v1, K6+K10 planted together | 0 | 2 | 0 | 0.08s | no |
| 02 | v1 both survivor files under python -OO | 1 | 2 | 0 | 0.29s | no |
| 03 | v2 both survivor files, normal | 3 | 0 | 0 | 0.39s | no |
| 04 | v2 both survivor files, python -OO | 1 | 0 | 2 | 0.30s | no |
| 05 | v2 + K6 | 1 | 1 | 0 | 0.07s | no |
| 06 | v2 + K10 | 1 | 1 | 0 | 0.07s | no |
| 07 | v2 + K6+K10 | 0 | 2 | 0 | 0.04s | no |
| 08 | v2 keep_scan users (survivor file + test_take_script_refusals.py) | 145 | 0 | 0 | 204.64s | no |

(1) K6+K10 together (v1): both fail, each with `assert ([], 0) == (['test_a'], 1)` at tests/test_survivor_keep_scan.py:27 (fold test) and :33 (glue test).
(2) v1 under -OO: both keep_scan tests fail with `KeyError: 'fold'` (line 27) and `KeyError: 'glue'` (line 33), because __doc__ is None so _SOURCES is empty. The r20 survivor test passes under -OO.
(3) survivor-tests-v2.patch: adds `import pytest` and a skipif marker (reason "python -OO removed the module docstring that holds the made-up sources") on both tests. Under -OO they SKIP (they do not run, so K6/K10 are not killed in -OO runs). Normal runs: 3 passed. K6 alone: fold test fails; K10 alone: glue test fails; both: both fail. `patch -p1 --dry-run` on a clean copy of the v1 file: applies. r20 file unchanged.
Mutants were planted in the copy only via exact string replace (K6: `if node.func.attr == "format":` -> `if False:`; K10: `texts = [_PLACEHOLDER.sub("", t) for t in _texts(node)]` -> `texts = _texts(node)`); keep_scan.py restored and cmp-identical to tree-C9 afterwards.
Slip: in run 05-07 my restore helper saved the already-mutated file as "good" once (a script bug); I re-copied from tree-C9 and verified with cmp; run 08 ran on the restored file. A first run 08 attempt on the mutated file was stopped and discarded.
Commands: cp -a tree-C9 tmp-C9/work; python -m pytest -q -p no:cacheprovider (TMPDIR=RR/tmp-C9/t PYTHONPATH=work/src, import path checked under work/src); python -OO -m pytest ... ; diff -u for the patch.
Logs: RR/out/C9/61ded9e-run0N-*.log. Patch: RR/out/C9/survivor-tests-v2.patch.
