# REVIEW.md round 21 cite check (agent aa983f6), saved by flows-audit; reviewer words unverified; static, no shell. 0 Blockers, 0 Majors, 2 Minor, 5 Nit. About 150 cites checked, newest cites MATCH (config.py:419-420, table.py:604, migrate.py grants, executor hooks agent_loop.py:886/901/909, 9 reconcile test assertions, demo cites). G5 patch not in patch-copies (consistent).
1 Minor REVIEW.md:117 "diff -rq showed only __pycache__" for /tmp/smfull: no evidence file shows it; tag UNVERIFIED like :121.
2 Minor no saved output for: git message "Context reduced to (1/1) to apply fragment at 392 / at 2" (:120); blank-line counts 53-16, 74-19 (:67, :134); "I ran wc -l" (:301).
3 Nit :200 stages.py:18-23 is_prod true for prod and any non-stage value, not "production only" (fix-review13.md:17 words it better).
4 Nit :202 _check_anchors at chain.py:440 not :443; chain.py:413-436 is _check_checkpoints.
5 Nit :131 evidence-13.md:63-73 covers only A-01 list test; test_p7_tick list test at :74-87.
6 Minor Decision 3 (:349) and 10 (:356) text omit the "this process does not sign" prerequisite and Decision 5 dependency (only table rows, X-5.1, X-5.3, Decision 5 say it).
7 Nit :347 criterion (8) garbled: "nothing in code or in the repository checks refuses a pilot config".
