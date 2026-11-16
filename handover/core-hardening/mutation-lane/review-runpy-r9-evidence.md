# run.py r9 independent evidence (EVIDENCE RUNNER, condensed copy of the report), 2026-11-16
Raw output: mutation-lane/evidence-r9-independent/ (index 00-TABLE.md). The runner records, it does not judge.

## Failures and deviations first
1. Full safety-tests.sh: no failures (root 0 of 416, non-root child uid 65534 0 of 61), 665 s.
2. `--restore --root <path over 4096 bytes>` ends with Python's own exit 1 and a traceback (OSError File name too long at root.is_dir()); the docstring says it never ends with Python's own exit 1. Same for a 120,000-byte root and for `--sha` as a 300-byte path value. r8 does the same, so not new in r9. `--file src/<120 KB>` and a 120 KB test path give INTERNAL ERROR plus traceback, exit 2, file unchanged. A literal 1 MB argument could not be passed (exec limit).
3. Plain `--restore` still exits 0 with planted text in two cases (the builder's own limit (d)): forged marker plus backup with a matching hash (N2, file holds `return 666`); marker forged with mode 0777 (N6, mode 777 written). With `--sha` both give exit 3 and the file stays planted.
4. A signal inside python start-up (0 to 0.05 s after launch of `--restore`) kills run.py with the default action (exit -15 or -2, one traceback line): marker stays, file stays planted; a follow-up `--restore --sha` restores it. Signals after the handlers exist always ended settled.
5. A root or file name containing a newline is refused by the import check (exit 2).
6. Lane originals changed during the run (builder started round 10 at 15:42 to 15:44 UTC); the "originals unchanged" check cannot hold for lane files; frozen and scratch copies match the r9 hashes.
7. ruff check run.py: 2 findings, both S603 (lines 759 and 1741), 0 noqa. ruff format --check: clean.
8. The new tests run against the frozen r8 code: 16 of 70 checks fail (T68, T96a, T96d, T96i, T96j2, T96l and others), so they do fail on old code; T96b3, c3, f, h2, l2 pass on r8.

## Passed
N0, N3, N3b, N4, N4b, N5, N5b, N6b, N7-N10 as designed; H3 refusals; H4 36 signal runs ended settled once handlers existed; banned scan 0 matches in 23 files; git status for src and tests 0 lines before and after.

## Not run
1 MB literal argument; SIGSEGV/SIGBUS, setsid escape, other OS, power-cut durability, other signals; a second full suite run.
