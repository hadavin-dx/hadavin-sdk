# Plan chain fix, review round 2 (egm-codebase-details), condensed copy, 2026-11-16
Read only; nothing run. 0 Blockers, 3 Majors, 5 Nits. Round-1 findings closed by reading (UNVERIFIED numbering, RENUMBER logic, edit 4, edit 21, script safety, edits 5/30, banner, PLAN-CHAIN:45, SUPERSEDED-INDEX:7) except C7b list items 2-3 (partly, N4).
M1 corrections.md:3 "the other 22 edits unchanged" is wrong: 8 replaced blocks (2,4,5,18,19,20,21,29) + added 30; use "the other 21 (18 unchanged, 3 renumbered)".
M2 DESCRIBE-ONLY-flaky-id-test.md:3 "about 1 in 2,731 (exact sweep: 24 of 262,144)": 262,144/24 is about 1 in 10,923; 24/65,536 is 1 in 2,731; "exact" overstated; same pair in patches-ready/README.md:62 and flagged in contradiction-checklist-v8.md:13.
M3 LEAD-CHECKLIST-v5.md:54,56,64 still name b0caeb84; final is 28f92c5d (owner: checklist v10 builder). A "verified" claim for 28f92c5d must rest on evidence-chain-r2.md, not Part F (builder's own run).
N1 apply-v10-after-chain.py:8-9,30-31 missing/malformed RENUMBER silently skipped; die() if absent; check each of edits 8, 13, 27 changed.
N2 :42/:16 check-then-write not atomic (use mode 'x'); edit files read with locale encoding, plan as UTF-8 (no live effect, edits pure ASCII).
N3 test-apply-v10-after-chain.sh:9 T3 label wrong (first 100 lines of the chained plan); script never compares out1.md to 28f92c5d.
N4 DESCRIBE-ONLY:12-14 item 2 firmer than item 1; align wording.
N5 SUPERSEDED-INDEX.md:25 cite independent sha256sum -c run (evidence-chain-r1.md Part D).
Not checked: section 5 totals recounted from rows, 780-line derivation, uniqueness of old text for 26 blocks, evidence-chain-r2.md, the stranger/citation reports.
