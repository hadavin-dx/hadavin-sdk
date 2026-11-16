# run.py round 5 builder report (condensed copy of the builder's hand-back), 2026-11-16
Nothing pushed by the builder, no spend, no real repo or real mutant run.
## Failures and uncertainties first
1. Two ruff S603 findings remain (run.py:419, :1115); no suppression added. Lead decides.
2. Several new tests do NOT fail on r4 code; they are guards shown to matter only via broken r4 copies: T61 (PYTEST_ADDOPTS/PLUGINS env, envleak mutant), T50 (unreaped), T51a (startcheck), T51b (worksin, memberstart), T43c (no mutant).
3. T47a injects signals in-process; T47b covers external signals.
4. A real memory-fault SEGV acts like SIGKILL: marker stays, --restore needed (documented).
5. N3: write path is dir_fd + O_NOFOLLOW protected; reads still by path (restore is hash-verified).
6. Builder slips: one run gave 278 PASS / 1 FAIL (T62b, bug in test snippet); parallel runs cross-talked via shared sleep patterns (fixed with private sleep binary); both logs kept as superseded.
7. N8 fixed, no test.
## Results (raw/)
Final run.py + safety-tests.sh: 279 checks, 0 FAILED (run-py-safety-tests-r5-new-final.txt). r4 code + final script (SKIP_T35=1): 41 FAILED, 235 PASS. r4 mutants: unreaped fails T50; startcheck T51a; worksin/memberstart T51b; envleak T24b+T61. sha256 list raw/run-py-r5-final-sha256.txt re-verified 0 mismatches. ruff: only 2 S603; format ok; bash -n and py_compile clean.
## Not run
Real mutants, real repo, repo test suite, bandit, non-root user, non-Linux, editable installs, real pytest @file, Python < 3.11, real SEGV, use inside a git repo.
## Next
Lead: decide S603; fresh independent security review (uncapped) and independent evidence run.
