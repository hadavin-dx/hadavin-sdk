# P1d-a plan pass 6 (rev 9) readiness review (egm:egm-implementation-readiness, agent a5b069d23c0f3e877). Saved as round7.
Result: NOT READY. 1 Blocker, 2 Major, 8 Nit, 1 note. Counts match (100 rows, 64 mutants, 722 samples, alphabets 72/66); mutant `old` unique; AST clauses, producers edits and DRIVERS entry consistent with the real files; P9 patch applies.
- F1 Blocker (221) round-trip clause "b holds no fixture secret (SV_B...)" cannot go green: a bare SV_B (22 chars) is never masked (HIGHENTROPY needs 40+; row H34b); ~69% of G-TXT-B texts hold SV_B; of the 28 differing texts ~19 hold SV_B in both a and b. P9 measured only "newly shown by the second pass: 0". Reword: "b shows no fixture secret that a did not already show".
- F2 Major (109, 331, 352) committed generated JSON (`p1d_a_base_rows.json`, `p1d_a_gate_base.json`) holds raw SV_B, EM and key-body pairs: gitleaks (default rules, whole history, no suppressions) trips; the parts rule covers source only. Store encoded or in parts and rebuild at run time, or commit hashes only.
- F3 Major (372-374) "hidden" undefined for reported-only shapes S7a, S8, S8b, S8c (S8b on base gives 3 under "output differs"). Define per shape: placeholder count new > base; list reported-only shapes.
- F4 (37) "BTK1, BTK2, MENT1 came out as written" unsupported: evidence is probes-r6 on the base gate; P9 Slack rows hand-composed, `_blocks` not called. Run on the P9 tree or reword.
- F5 (115) H27 spy clause vacuous: the spy sees the raw argument; the hook runs inside `redact_text`.
- F6 (221) `test_patterns_kinds` underspecified (set or list; entry split changes length; how to enumerate placeholder prefixes).
- F7 (331) DRIVERS entry needs a helper function, not a lambda (see p9_slack_driver.py).
- F8 (141-142) K43c, K43d "after" cells ambiguous (string body or expression).
- F9 (378) real-population differential names no tree: `handover/` likely absent on base `0dabf1f`; new fixtures join "tests"; P9 numbers not reproducible from the text.
- F10 CHANGELOG section unnamed; `sanitise_text` docstring wording unpinned; `redact_for_card` annotation (P9 Mapping vs `redact_text` dict).
- F11 "lines 580-588" for the quoted entries differs from disk: cite by name.
- F12 note: unprobed properties (differential, card-masks, only-rewrites-dots, default-unchanged, AST) show no definite failure by reasoning.
