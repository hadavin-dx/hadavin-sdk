# PR84 round 8, codebase-details (egm-codebase-details, sonnet), head 7e14096
Verdict: 0 Blocker, 0 Major, 3 Nit. PARTIAL REVIEW: read 1130 of 3284 diff lines in full; the rest (guard test, evidence_step.py) only grep-sampled. Ran nothing. Not a clean round on its own: a second pass on the unread part is needed.

Round-7 Majors: M1 (mask-pattern test uses monkeypatch, lru_cache cleared) FIXED; M2 (HADAVIN_REQUIRE_PINNED_UNIDATA written to GITHUB_ENV on the 3.13 leg only, guard rule 14) FIXED in form.
Unverified (stale checkout): tests/stage_mutants.py exists on real main; the variable's reader is truthiness-only.
Checked correct: step timeout sums (evidence 166 of 170 min, plan 11 of 15), Vault step identical in 3 places, exact-name container removal, Postgres bound to 127.0.0.1 (DSN uses localhost, very low risk), vault_target missing-token error + test.
Nits: (1) evidence.yml:350 "as in ci.yml" should read "same value as ci.yml"; (2) evidence.yml:333 and READER_RE line-based check still open from round 7; (3) very long comment line at evidence.yml:196.
