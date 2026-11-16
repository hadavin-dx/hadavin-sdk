# PR73 core/P3a-2 head c727453, codebase-details review, wave 2 round 1 (security path, uncapped)
Read-only reviewer, ran nothing. Verdict: 0 Blocker, 3 Major, 10 Nit.
- M1 Major: R4 is a real gap (killer uses a stub that answers by equality with the mutated constant; only a text pin sees the SQL; no real-server test flips only the grant option of an existing membership). Fix: H11 case with baseline `GRANT a TO b`, function body does `GRANT a TO b WITH ADMIN OPTION`, expect refusal; add the text-pin test to R4's killers.
- M2 Major: private process ids in public text (CHANGELOG: "layer 1 in the ticket P3a", "P3a-3", "order 89", heading "(P3a)"; migration_numbers.py lines 11, 26, 35, 37, 475, 483 incl. "R448"; tests: orders 112/132/140/186/89, BL-p3a2-001..003, G73-5, "round 2 of PR 73", "(P3a").
- M3 Major: CHANGELOG item 11 placeholder "LEAD TO FILL IN"; PG17 not run.
- N1 stage vocabulary: "every dev, demo or pilot database" -> demo or pilot.
- N2 migrate.py:439 uses \d (matches non-ASCII digits): use STEM from migration_numbers; `_label` duplicates `_esc`.
- N3 allow list matches trigger name only (see design F7).
- N4 released_problems(MIGRATIONS) vs patched _migration_files(): pass the same list.
- N5 four new noqa markers (S603 x2, S608, S324): remove; hashlib.md5(usedforsecurity=False).
- N6 migrate_mutants.py runner: copytree copies .env files and leaks on STOP (use try/finally, exclude .env*); `only in m.name` substring match; runner not in CI.
- N7 autouse role fixture alters schema owner and leaves a server-wide role; warn and refuse non-scratch.
- N8 previous-release test tautological on real files (labelled honestly).
- N9 evidence lint scope wider than CI; migrate-mutants log shows exit=0 though script returned 1.
- N10 spec drift against frozen ticket rev 10 (same as design F1).
- M88 survivor: mis-pointed killer, re-point to the line-426 test; M65 (current_user vs session_user) lost from the checked-in list: re-add. handover/tools/p3a2_mutants.py: mark superseded; plants into the live tree.
Not checked: no run; SHA-256 values of the released files; wheel packaging of the JSON lists; ticket lines 52-202; most of the ~5000 test lines; fail-before on ce70eb5.
