# fix-claims45: fixer report, CLAIMS-TABLE.md lines 300-600 (reader r45), round 2, non-security
Edited CLAIMS-TABLE.md and, forced by a check, RUNSHEET-WORDING.md (one new row A-034, status NO PASTE, and the count sentences). RUNBOOK.md and QUESTIONS.md untouched. Nothing committed.

## Gaps first (what I did not do or could not verify)
- Reader words were checked against files only where I cite it; I read mf.py:79-84, stage_server.py in full, n8n-published-numbers.md lines 1-35, RUN-ON-LAPTOP.md:50-60. I did not re-read the lane B rows outside the ones named below.
- Seven grades moved. They follow ONE rule I wrote into the verdict-words bullet (line 15): UNSUPPORTED only when no part of the sentence is shown true (a file supports one part and contradicts another = OVERSTATED); a sentence that no file supports in any part and that only a relayed number contradicts = UNTRACED with the relayed figure second ("by relay" is not a verdict). The lead must confirm each (marked LEAD CONFIRMS in the verdict cell). B-130 stays OVERSTATED (WL-16), not touched.
- I changed RW although the brief allowed that only when a check forces it. Forced: check_runsheet_paste failed ("claim ids missing: A-034") after A-034 became OVERSTATED, so row A-034 (NO PASTE, no string) was added. NOT forced but required by your "every sentence that states the totals": RW lines 33 and 498 and the status table (NO PASTE 22, total 217, section 1: 60). Revert those count edits if you want RW untouched; then RW states the old totals.
- Minor findings: all handled without re-review (list below). Not re-read by a fresh reviewer.

## Regrades (all LEAD CONFIRMS)
| id | old | new | why |
|---|---|---|---|
| A-001 | UNSUPPORTED | OVERSTATED | scenes 1-4 part supported, scene 5 contradicted; same shape as A-008/A-005/A-084 (M1) |
| X-1 | UNSUPPORTED | OVERSTATED | own cell says the "no lead data" half is supported (M6 rule) |
| B-101 | UNSUPPORTED | OVERSTATED | second clause supported by mf.py:83, review-as-final-state contradicted (M6) |
| A-034 | SUPPORTED | OVERSTATED | same dependency (T12/P1) as A-033, A-035 (M2) |
| A-043 | SUPPORTED | OVERSTATED | alert_sent needs v4 table and state unknown needs P1, as A-012, A-057 (M2) |
| A-087 | OVERSTATED | UNTRACED | no file supports any part; only relayed 45 s figures speak against it (M4) |
| B-197 | OVERSTATED | UNTRACED | file itself says NO MATCHING ROW; 0 of 15 is quoted/relayed, raw not seen (M5) |

## Findings
- M1 FIXED (A-001 regraded, above).
- M2 FIXED (A-034, A-043 regraded; A-033/A-035 unchanged).
- M3 FIXED by reason, no regrade: A-014, A-018, A-037 now say why OVERSTATED (flow files support part: repeat path never reaches SubInput/RunSub, takeover path, ClaimStuck excludes unknown); A-099, A-100 say why UNTRACED (whole sentence is the outcome of a recording that does not exist; line 15 already names A-099).
- M4 FIXED. A-017, A-051 stay OVERSTATED with the stated basis "more than lead answer 17:05Z allows" (line-15 clause, as A-097); A-073 stays OVERSTATED, basis: P:120 and P:149-161 of the same file disagree; B-032, B-056 (same claim) stay OVERSTATED, basis: REC Every30s/ClaimStuck support the 30 s pickup; A-087 -> UNTRACED. No cell says "by relay" as a verdict any more (grep: only the line-15 sentence that says it is not a verdict, and line 162 text on a different phrase).
- M5 FIXED (B-197 -> UNTRACED; Table 2 row 74 text aligned). Reader's "UNSUPPORTED" contested: a relayed 0 of 15 cannot make a sentence false in this checkout.
- M6 FIXED: separator written in B-062 and A-083 cells and in line 15 (A-083, A-098, X-4, B-093 to B-095 stay UNSUPPORTED: no part true); X-1 and B-101 regraded.
- M7 FIXED: line 469 rewritten (one rule: RW wins; the wording that agrees with RW wins); A-025 removed from "against row 20" (row 20 holds A-026 only, A-025 has no row).
- M8 FIXED: A-040 safe wording drops "safe"; A-084, A-030, A-021, A-077 got explicit conditions (crop/P1/stop lands inside the mail step); A-001, A-008 verdict cells and safe wording say HELD until P4a (HubSpot node never ran). A-084 partly contested: its string already says cropped or hidden; condition added anyway. String edits: none (paste strings unchanged, pair check passes).
- M9 FIXED: A-083 cell, Table 2 row 42 and line 365 now say the named wait is the D2 decision on A-073a, and that A-073c pasted or A-073b not applied also give 20.
- Minors fixed: A-016 verdict reason; A-050/A-036 order rule; line 487 vs A-004 (head in first pass, read in full round 29); row 51 B-045 says it was read in stage_server.py, not run; line 365 status counts recounted from RW (PASTE 55, DELETE 30, HELD 96, NO PASTE 22, SUPERSEDED 14, 217 rows); line 492 now points to the one definition instead of redefining.

## Commands (after edits; raw tail)
- python3 claims-count.py CLAIMS-TABLE.md -> OVERSTATED 110, SUPPORTED 78, RELAYED-ONLY 57, UNTRACED 79, UNSUPPORTED 6, total 330; lanes A 100, B 226, X 4; to-do rows 87; offenders 0; ids 330 unique 330.
- My group script (scratchpad, ids of every to-do row): with a row 97 = 75 O + 6 U + 15 T + 1 R; rowless 233 = 78 S + 56 R + 64 T + 35 O. Lane split A 18/23/50/2/7, B+X 60/34/60/4/72 (S/R/O/U/T). Sentences updated: lines 15, 62, 117, 122, 123, 128, 171, 218, 365, 623, lane A block, Part 7, verdict list rows 1, 3, 44, 58, 74, Table 2 row 74; RW lines 33, 48, 498.
- check_rw_ct_pairs: found 144, "not found in CT: 0". check_runsheet_paste: total rows 217, 113 flagged, no missing, RESULT PASS. check_refs PASS 5190; check_names PASS 655; check_secrets PASS 0 hits; check_counts PASS 52 files / 655 nodes. ruff format --check . (in flows-audit): 1065 files already formatted.
- No secret, personal e-mail or GitHub handle added (grep: none).

## For the lead
- Confirm the seven regrades (or tell me which to revert; each revert moves counts by one and needs the same sentence list).
- Open choice not made: whether B-032/B-056 should be UNTRACED like A-017/A-051 would be if the lead-answer clause is rejected.
