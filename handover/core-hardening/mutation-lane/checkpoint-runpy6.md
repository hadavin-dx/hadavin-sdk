Checkpoint (run.py round 5), 2026-11-16, started 
Done: r4 copies kept in raw/.codecopies/run-r4.py and safety-tests-r4.sh; read run.py, safety-tests.sh, review r4, independent evidence.
Next: edit run.py (M1-M3, N1-N12), add T47+ to safety-tests.sh, run new code, run r4 code (must fail), mutants of r4 for strengthened tests.
Blockers: none yet. No commit (instruction).
Checkpoint 2: run.py and safety-tests.sh edited (M1-M3, N1-N12, T47-T61); first full run on new code: 272 PASS 1 FAIL (T61 test-file slip: PYTEST_VERSION is set by pytest itself, fixed). Next: final r5 run, r4 run, r4 mutants for strengthened tests, REPORT.
Checkpoint 3: added mount refusal, private sleep name for parallel runs (cross-talk found: first parallel run had 3 false FAILs), T62. Running r5 final, r4 code, 2 r4 mutants; 2 more mutants after. Next: REPORT-runpy6.md, sha256.
Checkpoint 4 (12:12): r4 mutants confirm T50, T51a, T51b discriminate. Final r5 run + r4 re-run in progress; then raw files, sha256, REPORT-runpy6.md.
