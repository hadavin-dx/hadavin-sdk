# Fresh review of lane3-fix-8-r2.patch (sha256 0c976b13...), reviewer egm:egm-codebase-details, read-only, ran nothing; saved by the lane 04:13Z
Result: 0 blocker, 0 major, 2 minor, 2 nit.
Spec 1 and 2 (code): PASS by reading. domain_labels_ok (identity.py:100-114) matches; plain_address_ok (:117-120) requires exactly one '@'; all 5 callers (smtp_outbox.py:92, :217; config.py:509; smtp_provider.py:102, :229) use it; sweep of src/ and scripts/ found no other '@' parsing that bypasses it.
Spec 3 (tests): fuzz tests assert counts on both sides (>200 accepted, >5000 rejected of 30000); third fuzz guards over-refusal; per-class tests present; nothing weakened that the reviewer could see (no diff against r1 done).
Spec 4 (docs): limits.md:26, contract.md:28, tests.md:131 match the code; plain wording.
Findings:
1. Minor, contract.md:28 vs limits.md:26 and tests/test_domain_labels.py:163-164,196: the sentence "the same label rule refuses the sender, recipient and reminder addresses" can be read as "these also need a dot"; code accepts `reminder@localhost` on the plain path (test pins it). Add one sentence: a one-label host such as localhost is accepted for sender, recipient and reminder; the dot rule is for the lead email only.
2. Minor, raw/b10-mutants.log lines 8 and 14: two survivors unexplained; 14 (rpartition -> partition on the lead path) is equivalent (_EMAIL_RE forbids '@' in domain); mutant 8 "empty label allowed" survived while line 19 of the same name was killed: the log does not say which variant is which. Record why or show equivalence.
3. Nit, tests/test_domain_labels.py:137,142: `domain` computed only to feed `assert domain is not None` (vacuous): delete both lines.
4. Nit, tests/test_domain_labels.py:91: oracle shares DOTS/hyphen constants with the code and its forbidden-character rule (isspace or ord<32) differs from the code's (\s and category C); zero-width characters not in the fuzz alphabet (other tests cover category C). Acceptable; no change required.
Could not check: any run, hygiene scan, ruff/bandit, fails-before log, final full run, diff against r1.
