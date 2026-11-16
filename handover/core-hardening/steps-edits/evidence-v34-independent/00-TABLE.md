# Evidence v34 independent (EVIDENCE RUNNER: runs and records, does not judge)
Run 2026-11-16 (UTC). Work copy: w/ (613 top-level files copied from steps-edits; sha256 of copy equals originals: 00-sha-*.txt, diff empty; copy still identical after all runs).
| # | Command (in w/) | Result | Raw file |
|---|---|---|---|
| 1 | python3 -B build-v34.py | exit 0, built 10 pages | 02-build.txt |
| 2 | python3 -B check-v34.py | exit 0, "check-v34: 0 failure(s)", 0 FAIL lines | 04-check.txt |
| 3 | python3 -B -I v34-fail-proof.py | exit 0, none fails on v34; 30 checks do not fail on v33 (listed with reason in v34-CHANGES.md, not verified by me) | 05-failproof.txt |
| 4 | python3 -B gap-proof-v34.py | exit 0, v33 checker misses 4 of 15, v34 checker misses 0 of 15 | 06-gapproof.txt |
| 5 | heavy-slot.sh python3 -B mut34.py | slot 2 taken 19:30:04Z, exit 0, baseline failures 0, 300 plants: 299 caught by meant check, 0 missed, 0 anchor-not-found, 1 negative control printed MISSED as it must | 07-mut34.txt |
| 6 | wc -w | see below | 08-wc.txt |
| 7 | banned-vendor scan (list read from tests/test_no_reference_material.py at run time) | 10 terms loaded, 24 files (v34 files + LEAD-RELEASE-NOTE-v18 and its source), 0 hits | 09-scans.txt |
| 8 | strict secret-shape scan, same 24 files | AKIA/github/sk/slack/private key/jwt/12-digit/40-hex: 0. email-shape: 11, all at example.com with 2-char local part. base64-shape 40+: 1, in check-v34.py (lowercase code text, not a secret shape) | 09-scans.txt, 10-scan-detail.txt |
| 9 | time pairs | 18:29 UTC=23:59 IST, 18:19=23:49, 18:04=23:34 all correct by arithmetic; no UTC/IST mismatch found in the 8 pages | 11-timepairs.txt |
| 10 | 7 hostile edits of built pages, one at a time on a scratch copy | 7 of 7 caught by check-v34.py (2 first tries did not apply, redone) | 12-hostile.txt, 13-hostile-b.txt |

Word counts (wc -w): SHEET-A 6277, CARD-A 2211, APPENDIX-A 5753, SHEET-B 6078, CARD-B 2126, APPENDIX-B 5684, FILM 577, HELPER 897. Five-page totals per check C07: A 15715, B 15362.

Hostile edits: H1 card A IST 23:59->23:58 (C01,C04); H2 helper 18:19->18:20 (C01,C249); H3 appendix B 18:04->18:05 UTC (C01,C04,C210); H4 sheet A delete first line naming card/appendix (C01,C14d,C147,+1); H5 film page "and sheet B" removed (C01,C238); H6 sheet B USD 189.00->198.00 (C01,C04,C48); H7 card B 18:29->18:30 UTC (C01,C04).
Observation: C01 (rebuild-and-compare) fires on EVERY edit of a built page, so these 7 edits test C01 first; the other checks that also fired are listed above. An edit made in the source or facts AND rebuilt is what mut34 covers.
