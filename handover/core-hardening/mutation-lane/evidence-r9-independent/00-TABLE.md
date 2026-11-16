# evidence-r9-independent (EVIDENCE RUNNER; records, does not judge)
Inputs: run.py c81a7ba9...9e6a, safety-tests.sh b498dd03...5cbc = builder's hashes = evidence-r9/frozen/. All runs used byte-identical copies in the session scratchpad (r9-indep/in). The lane originals were edited by the builder at 15:42-15:44 UTC (round 10 started), so the lane files now have other hashes (hashes-after.txt); frozen copies unchanged.
| check | exit | result | file |
|---|---|---|---|
| full safety-tests.sh (root + child uid 65534), 665 s | 0 | root FAILED CHECKS 0 of 416; child 0 of 61; skipped none | full-run.txt, .exit, .timing |
| ruff check run.py (repo pyproject config) | 1 | 2 findings, both S603 (lines 759, 1741); 0 noqa in file | ruff-check.txt |
| ruff format --check run.py (repo config) | 0 | already formatted | ruff-format.txt |
| bash -n safety-tests.sh | 0 | no output | bash-n.txt |
| negative controls N0-N10 | see file | see report | negative-controls.txt |
| hostile inputs H1-H3 | see file | see report | hostile-inputs.txt |
| signals during restore H4 (36 runs) | see file | see report | hostile-signals.txt |
| T42 T51 T68 T96 against run.r8.py | 0 | FAILED CHECKS 16 of 70 | new-tests-on-r8code.txt |
| banned scan | 0 | 10 entries read, 23 files, 0 matches | banned-scan-counts.txt |
