# PR 83 (P0t follow-up) @e2d8971: round 2, implementation-readiness review (condensed by the coordinator, ids kept)
Verdict: NOT mergeable today; blockers are missing evidence, not wrong code. Ran nothing. Evidence dir holds only targeted-313.log and targeted-312.log (734 passed, 3 skipped, 2 deselected).
F1 Blocker | no full suite (with Postgres) or perf at e2d8971 on either python (q281 admits). Run both at the final head.
F2 Blocker | stage mutants T1-T14 (51 total) not evidenced at this head on either python.
F3 Blocker | no fail-before: tenant tests fail on main only by ImportError; none for rewritten scanner/changelog tests or the one-occurrence budget. Save fail-before for the three test files; rely on T6/T10/T14 for behaviour once F2 runs.
F4 Blocker | order says refuse at tenant creation and config validation; diff adds a type nothing uses. Record the path check (AST walk + grep: redact.py, runmap.py, gate.py only mention tenants as label/placeholder) and ask lead to accept "no path exists; check is a type for the first tenant field". UNVERIFIED lead accepts.
F5 Major walk matches only "tenant" names. F6 Major "2 deselected" unexplained, tree-clean=0 ambiguous; log exact command and ids. F7 Major no lint evidence at head (ruff, format, bandit, scan_repo, hygiene); long lines may fail format. F8 Major three duplicate tsv rows; confirm each matches two real occurrences.
F9 Minor CHANGELOG long line. F10 Nit wording done and pinned.
