# fix-rwct40: RW / CT round 40 fixer (input: reviews/rw-ct-reader-r40.md, M1 to M9)

Files edited: RUNSHEET-WORDING.md (RW) and CLAIMS-TABLE.md (CT) only. Nothing committed. No secret or personal handle printed. EGM skipped for the checking of reviewer words: this is a non-security fix pass beyond round 2 (Blockers and Majors only), run by the lead's order.

## Not fixed, left to the lead (listed in CT, bullet after the "Mixed verdicts" bullet)
Each would add a new RW row (new wording) or move the totals, so it is a lead choice:
- M1: the first-phrase rule is broken by B-039, B-048, B-052, B-078 (SUPPORTED with an unproven second part) and B-099, B-104, B-106 (RELAYED-ONLY with an unproven second part). The reviewer is right on the text. Regrading all seven would give SUPPORTED 81, RELAYED-ONLY 61, OVERSTATED 96, and six of them (not B-078) need a new RW row. Left as is, listed.
- M2: B-073 (UNTRACED while two READMEs exist and disagree): reviewer right on the definition; I fixed the false words "no file shows a run or a non-run" and left the grade (a regrade needs an RW row). B-086, B-126, B-140: the OVERSTATED grade was a deliberate choice of fix-rwct15 to match A-010, A-045, A-074 (A-010 has a flow reading: saveData none). Left, listed with the alternative.
- M4: B-105, B-111, B-114 (number disagrees with its source) would be OVERSTATED and need RW rows; B-110, B-112 would be SUPPORTED because the probe file exists and was read. The whole RERUN family was graded RELAYED-ONLY by an earlier choice. Left, listed.
- Open items that need the owner or a third party: none new. The desk repository (needed to verify the desk strings) is not in this checkout: the lead verifies at re-pin (already the rule).

## Fixed
- M3 (real, fixed, class: a sentence about the take's stage or the desk key file graded SUPPORTED on a stand-in): B-043, B-047, B-135 regraded SUPPORTED to UNTRACED (same as B-030, B-045, B-049, B-014). No RW row needed. Every count and lane split repeated in CT (lines 15, 116, 121, 122, 170, 218) and RW (33, 483) updated, plus a Round 40 line in the UNTRACED bullet.
- M5 (real): hedges put inside the Paste cell itself, identical in RW and CT: B-016, B-019, B-038, B-088, B-092 (B-038 was not in the reviewer list but is the same class). B-130: the flat negative "AF2 is not run" now says "No file we read shows that ... (AF2) was run".
- M6 (real): "five cells" was wrong, the B-024 string has six parts and the plan row has seven cells (the seventh, NEEDED, stays); fixed in RW line 12 and the B-024 row. B-016 and B-019 strings no longer repeat the words of cell 1 and the Goes-where cell says so.
- M7 (partly wrong): the reviewer's "RW status table says 15" is wrong (the 15 is in CT only); but "15 rows with no lane row" was also wrong: by script RW has 31 ids that are not CT lane-table claim ids, 15 have a bullet, 16 have none. CT now lists the 16 by exact id: V-11, V-57, V-41, N-3, P-155, X-5a, X-5b, N-4a, N-4b, N-5b, N-5c, N-1, N-1b, N-8, N-11a, S5-c. The reviewer's 9 were all in that list. The 330 total is unchanged; no lane row added.
- M8 (real): CT B-003 now says B-003c is "SUPERSEDED (its Paste cell says NO PASTE)", as RW does; CT B-046 now says its RW status is HELD, applied as a delete only together with B-045.
- M9 (real): RW History line and the "Not reviewed in their final form" bullet rewritten with the real latest fix (fix-rwct40, after fix-rwct39) and read (r40), the lines read r40 did not read, and the rows changed now. The outside-file definitions (read r34 M2, Q31 item 76 (a), NQ-1) are named with their file; I did not copy their text into RW.
- Minor: N-13 is now a tag everywhere (RW line 191 and the exact-current cell "(no tag today)" of N-12 and N-13).

## Counts
Before: SUPPORTED 88, RELAYED-ONLY 64, OVERSTATED 89, UNSUPPORTED 10, UNTRACED 79 = 330 (lanes A / B+X: SUPPORTED 21 + 67, UNTRACED 11 + 68).
After: SUPPORTED 85, RELAYED-ONLY 64, OVERSTATED 89, UNSUPPORTED 10, UNTRACED 82 = 330 (SUPPORTED 21 + 64, UNTRACED 11 + 71). Flagged A/B ids stay 96; UNTRACED A/B ids 78 to 81, of which with no RW row 65 to 68. RW rows stay 199, ids unique 330.

## Raw last lines of the checks (run after editing)
- check_rw_ct_pairs: `paste strings in RW: 144 | found word for word in CT: 144` / `not found in CT: 0`
- check_runsheet_paste: `claim ids marked UNSUPPORTED, OVERSTATED, DELETE or STALE ... 96 | with no row here: []` / `claim ids marked UNTRACED there: 81 | with no row here: 68 ...` / `RESULT: PASS`
- claims-count: `verdicts: {'UNSUPPORTED': 10, 'OVERSTATED': 89, 'UNTRACED': 82, 'SUPPORTED': 85, 'RELAYED-ONLY': 64} total 330` / `offenders: 0 []` / `ids: 330 unique: 330`
- check_refs: `PASS 5192 references`
- check_names: `PASS 655 rows`
- check_secrets: `PASS 0 hits in 2838 files`
- ruff format --check .: `963 files already formatted`

Not checked: whether the desk strings are true (desk repository absent); the CT and RW lines the reviewer did not read were not re-read by me beyond the edited lines.
