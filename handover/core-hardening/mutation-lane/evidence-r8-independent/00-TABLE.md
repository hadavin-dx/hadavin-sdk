# evidence-r8-independent (EVIDENCE RUNNER, no judgement)
Frozen inputs (byte-identical copies in the scratch dir; lane copies run.r8.py / safety-tests.r8.sh have the same hashes):
run.py 39059b7c5a1dc031cf1b47ab6fe2242f8c0c09e4afc1c1763a51fa52d897e009 ; safety-tests.sh 6915bbe96fdbcd61d3e65c941ae06cdf94c0761cd70a54834febc03ffbfffd92
Attempt 1 (INVALID-attempt1-*.txt): run on the lane files; another session edited lane run.py (14:33) and safety-tests.sh (14:35) during the run; hashes no longer match. Discarded.
| command | exit | FAILED CHECKS | file |
|---|---|---|---|
| full safety-tests.sh, root + non-root child (frozen r8) | 0 | root 0 of 395; child (uid 65534) 0 of 41 | full-run.txt |
| new-test blocks (T17 T69 T76 T77 T79 T87-T95) vs r7 run.py (sha 01a741d2...) | 0 | root 31 of 61; child 33 of 67 (as printed) | new-tests-on-r7code.txt |
| ruff format --check run.py | 0 | - | ruff-format.txt |
| ruff check run.py | 1 | 2 findings (S603-type, no noqa) | ruff-check.txt |
| bash -n safety-tests.sh | 0 | - | bash-n.txt |
| ast parse run.py | 0 | - | py-compile.txt |
