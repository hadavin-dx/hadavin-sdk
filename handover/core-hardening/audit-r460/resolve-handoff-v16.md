# Resolve, hand-off v15 reviews (security round 4, readiness round 4). Hand-off v16.

Status words: FIXED-IN-TEXT (where; the product code and tests do not exist), RUN (a raw file shows it on 16.15 with reference code), OWNER-ONLY, LEAD-ONLY. Nothing is "verified" beyond the evidence named. The EGM resolve skill was not invoked (not available to this agent); the lead runs it. Every finding id is mapped with its test in `v16-CHANGES.md`.

## Security (0 blockers, 6 majors, 8 minors)
| Id | Status | Where |
|---|---|---|
| Major 1 | FIXED-IN-TEXT; reference code RUN (K1 to K6, K8, K9: the old shape accepts -1, the v16 shape raises and rolls back) | 5.4 item 4b |
| Major 2 | FIXED-IN-TEXT; reference code RUN (L1 to L5: the real `Limits.blocked` raises on NaN, the v16 shape returns `bad_amount`) | 5.4 item 4b |
| Major 3 | PARTLY: password logins and two runs (175 of 175, Q1 to Q5) are the builder's own; the independent re-run on 14 and 17 is LEAD-ONLY (L18) | 7.2, section 10 |
| Major 4 | FIXED-IN-TEXT (credential policy, operator-only secret, TEMP check, negative tests); RUN P1 to P7, G1 to G8, J1 to J3; the code is owned by the DB-2 PR and not written | 5.5b item 6, 5.6 (g2) |
| Major 5 | FIXED-IN-TEXT (kill-switch record, RUN M1 to M9); L-2 has a dated design (5.10b); the control itself is not built and needs the lead (core resumed) | 5.6 (m), 5.10b |
| Major 6 | FIXED-IN-TEXT; guard prototype RUN O1 to O3 with 13 mutants | 5.6 (j) |
| m1 | FIXED (deviation vi) | 5.6 (n), section 5.6 item 1 |
| m2 | FIXED-IN-TEXT; RUN N1 to N4; needs L7's own yes | 5.6 (k) |
| m3 | LEAD-ONLY (L18) | section 10 |
| m4 | FIXED-IN-TEXT; RUN H1 to H5; the owner can still disable the trigger (H4, stated) | 5.6 (l) |
| m5 | PARTLY: alarm owner is L13 (lead); size measured 110.6 B per row | section 10 |
| m6 | FIXED-IN-TEXT; reason codes of all detectors UNVERIFIED (builder lists them); v15's CHANGES row was wrong and is corrected | 5.3, `v16-CHANGES.md` |
| m7 | LEAD-ONLY (L19) | section 10 |
| m8 | PARTLY: breaker specified; it does not change the daily bound; question O1 stays owner's | 5.3, 5.9 row 8 |

## Readiness (0 blockers, 5 majors, 9 minors)
M1 to M5 and minors 1 to 8: FIXED-IN-TEXT as the table in `v16-CHANGES.md` says (one `Gate` protocol; audit-reader code owner named; inline `ALTER TABLE` and real node ids; complete hot-file lists; `gate4.sh` run once and E0-S1-5 repointed). Not code: none of it exists, so every test is planned. M5 (S-1 size) is LEAD-ONLY (L21). The unverified items now have a table with a way to settle each (section 10).

## Baseline, found while running `gate4.sh`
`pytest` on the unchanged tree: 2 failed (guard tests that read `handover/` files outside my folder). LEAD-ONLY (L20). I did not edit them.

## Orders
L7, L9, L16, L17 OWNER-OPEN, not assumed. Reader = audit reader role (L12). Q34 default file kept exact (`CHECK (usd >= 0)`), applied only on an owner yes. Q24 no second vendor account (nothing here adds one). Q28 D5 non-blocking, core paused.

## Independent evidence of v15 (read last)
`evidence-handoff-v15-independent/00-SUMMARY.md` did NOT exist at 16:58 UTC (I waited about 10 minutes with a bounded poll; the independent run was still going). I therefore read its raw files instead, as they stood: `raw-indep-baseline.txt` ends `SUMMARY pass=122 fail=0`; `raw-indep-mutations.txt` lists 33 mutants of the v15 held files, every one CAUGHT, none survived; `raw-sha-match.txt` matches the three v15 sha256 pins; `raw-banned-indep.txt` has 0 hits in 26 files. These concern v15's held files; v16's DB-2 file has a new hash by design (4c37aea8...) and its checks are my own runs, not independent. **Nothing in these files asks for a change, but the summary (the judgement) is unread: LEAD-ONLY, read it when it lands and send what it lists.**
