# A19fix2 checkpoint 1
done: B1 leak proof on old code (handover/evidence/A19/fix2-b1-leak.txt: sharp s, capital sharp s leak in clear; Cf ids leak through bare redact()); fix in stages.py (id read as written against ASCII class), textfold.py leaf (M1), tests (N1, N2, property sweep, AST import test, M2 punctuation ids); new tests fail on old src (9 failed) and pass on new (80 passed).
next: mutants for new rules (T32 re-point, T4 re-point to textfold, T34/T35), CHANGELOG, A19fix.md count (N3), then gates on final head, commit, push, report.
blockers: none. commit sha: not yet.
