# EGM review round 2 of at most 3: tickets/F-store.md, section "RESOLUTION of review round 1" (ordered by the lead in ORDER 010 item 5, alongside the build)
When: 2026-11-20 05:51 to 05:57 UTC. Reviewers: egm:egm-implementation-readiness = completed; egm:egm-codebase-details = completed (model fable, direct dispatch, through the Skill tool). Nothing run by either.
Round result: NOT CLEAN. Blockers 3 (two of them the same), Majors 12 (five raised by both), Nits 17. No round-1 answer was contested by me; five round-1 answers FAILED (file list, run cost, expiry age, one numbering, the isolation test).
Resolution: ticket section "RESOLUTION of review round 2" (Q1 to Q10) and two messages to the running builder (05:54 and 05:57 UTC) with the same content.

| id | severity | finding (short) | answered in |
|---|---|---|---|
| ir-2-1 / cb-2-B1 | Blocker | the file list misses three existing test files that break: tests/test_audit_drain.py (pins the last tick step in 6 places), tests/test_k5_fixes2.py (renamed-tree helper stops at the new GRANTS row), tests/test_stop_state_roles.py (applied list after the upgrade test) | Q1 |
| ir-2-2 / cb-2-M1 | Blocker / Major | the changed settle claim cannot tell whether the row was open or expired, and the delta depends on it; a plain read first races with the expire step and can lower a booking after expiry | Q2 |
| ir-2-3 / cb-2-M3 | Major | expiry age: which agent, float against int, and "never expired while the run works" is not true (the stuck age is a quiet-time bound) | Q3 |
| ir-2-4 / cb-2-M2 | Major | R3 and R14 cb-2 contradict each other on "expired, settled lower"; C5, mutant 13, invariant 3 and the README still carry the old meaning | Q4 |
| ir-2-5 | Major | the three design changes have no test cases (run cost, applied flag, age) | Q5 |
| ir-2-6 | Major | README and ii-meter.md number the contract differently | Q6 (done: README 2.2 points to ii-meter.md) |
| ir-2-7 | Major | README 2.1 did not match the resolution in five places | Q6 |
| ir-2-8 / cb-2-M6 | Major | the evidence command names files the resolution renamed and skips the crash, role and pin tests | Q7 |
| ir-2-9 / cb-2-M4 | Major | "T1 asserts SHOW transaction_isolation" proves nothing; no mutant for the SET | Q8 |
| cb-2-M5 | Major | after "expired, then settled lower" the row says less than the counters hold; counters cannot be reconciled from the table | Q9 |
| nits | Nit | cb-4 contradicts R1; N8 conditional; phases; rollback wording; helper name; purge line position; stale status lines; seed order; which-mapping KeyError; scale bound; audit after commit; zero delta; line numbers; docs outside R1 | Q10 |
Confirmed by the reviewers (no finding): no deadlock cycle (settle: reservation row, day, month, runs; reserve: its row, day, month); two concurrent settles of one id change the books once; the CHECK constraints hold in every allowed state; R2, R4 to R9 hold as design.
