# Questions for the lead (lane 3)
2026-11-13 12:42Z: 2 UNEXPLAINED error marks (`E`) in the PR #12 (8d65577) run 2 full suite, raw log handover/demo3/evidence/raw/suite-pr12-run2.log (`-q -rs`, basetemp outside TMPDIR, no traceback saved). By position they fall in tests/test_fakes_body_before_answer.py (mapping unreliable). Not reproduced in 10 later full runs. Proposal: Q10 = that file x20 in lockstep with a second suite on 8d65577. Default taken if no answer in 20 min: start Q10 when the load is under 4.

## 2026-11-13 13:40Z Q-19: addresses `loc@.dom` and `loc@a..b` are accepted
Found by Q2b (identity-fuzz-b.md classes leading-dot-domain, double-dot-domain): the desk accepts a domain that starts with a dot or has two dots in a row and treats it as its own lead. Trailing dots go to review. Is accepting these wanted? Default: leave it (product behaviour, not a documentation fix); not documented as a promise.
