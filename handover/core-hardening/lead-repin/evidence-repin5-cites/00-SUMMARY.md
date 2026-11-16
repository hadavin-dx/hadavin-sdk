# Citation check of LEAD-REPIN-VERIFY.md (guide v5) and v5-CHANGES.md
EVIDENCE RUNNER, 16 Nov 2026. Read-only on everything outside this folder; no network, no spend. Judges nothing: the verdict column compares text only.
Table: `cites-table.tsv` (78 rows). Counts: **match 68, no-match 4, cannot-find 6**.

## Failures first
No-match (4):
- Row 11: guide l.93 says "the v4 guide said 0.57 to 0.70 s for 1 MB". The v4 guide says "about 0.5 seconds"; 0.567 to 0.697 s comes from evidence-repin4 and review-repin4-citations.md l.16.
- Row 25: guide l.116 lists delete word `clean`; the script (l.1180, DELETE_RE) uses `clean.?up`. (The hand command on guide l.135 uses `cleanup`.)
- Row 40: guide l.53 says release note v8 G12 "line 33" says a gap longer than the lease is not claimed. Line 33 only says "the ban list and lease sentence of section 5 decided"; the sentence is on line 123.
- Row 60: guide l.49 calls G1 to G38 the numbered gates; v8 has G1 to G42.
Cannot-find (6):
- Row 3: neither file states a sha256 of the script, so there is no guide value to compare (the only statement is evidence-repin5/08).
- Row 15: guide l.95 "the independent run found 3 of those (v4's 7) missed or mis-read": the independent table lists its own 28 mutants (7 not caught: m05, m09, m13, m26, m27, m28, m19); no mapping to the builder's 7 other than m3.
- Row 33: review-codebase-1.md is not in the checkout (the guide says so).
- Row 71: "End-date refusal: shown" exact wording not found in v8 (l.61 names the line; "Spend lock: shown" is at l.87).
- Row 77: what lines 1045-1056 and 500-512 of the test program say: code not in checkout.
- Row 78: BL-wp6-G1 row in the studio problem list: not found in core-hardening.

## Recomputed from the script
- sha256 of lead-repin-verify.sh: 3dfebbce5c14ac2bd80257efee62091bc09d2086f1ab0855ee5a380544e4d72e (1572 lines); equals evidence-repin5/08. My copy had the same hash and was deleted after the run.
- `--self-test` on a copy: bash `SELF-TEST: passed=1022 failed=0`, rc 0 (selftest-bash.txt); dash the same, rc 0 (selftest-dash.txt). Guide and v5-CHANGES say 1022: match. 21 machinery lines are PASS (machinery); all 1022 counted.
- v5-CHANGES "388 of the v5 checks fail against v4": evidence 01 shows passed=610 failed=388 (998 checks, not 1022; the claim does not say otherwise).
- Mutation count: 14 damages x 2 shells = 28 runs, as stated; v4 had 7 x 2 = 14, as stated.

## Not checked
Meaning of any code line outside the checkout; whether each G/R row says what the guide builds on it beyond the quoted words; guide text on v9/v10 and owner sheet v25-A/v26-A (newer files exist beyond v9/v25-A that the guide names); no banned-string scan was run on this folder (only counts would be needed; not done). Stray processes: none started; /tmp has no lead-repin.* folders left.
