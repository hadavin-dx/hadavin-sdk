# fix-contra2 (fixer, 2026-11-16): findings of reviews/contra-vs-decisions-r2.md that touch CLAIMS-TABLE.md, RUNSHEET-WORDING.md, flow-check/README.md, patch F-008 comment
Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-contra2/ (all four files). Reviewer words were checked against the text first; all items below were real.

| Item | File and lines | Done |
|---|---|---|
| 8, 23 | flow-check/README.md item 4 (saved runs) | "must be deleted at clean-up" replaced: the take never deletes saved runs, no owner step does (Q19-1). Header: run_all.sh film-v5 block and --baseline marked PARKED by Q17-2; take_check.sh is the one live tool. Not touched: the option text for --baseline and the run_all.sh command line (still describe what the code does). |
| 5 | patches/F-008 comment line 11 | reworded, no delete promise; one '+' line changed, hunk counts unchanged. |
| 10 | RW 57, 58, 70, 77 | caption offers removed; A-017b, A-019b, A-081b (and A-073b, A-076a, A-076b, A-081a) listed as CUT, D2 moot. Rows 160, 172, 217 already carried the CUT note; kept as audit trail. |
| 11 | CT 183, CT 406 (A-087 row), RW A-087a/b (143-144) | one text everywhere: "At 45 s the recovery time is not measured ..." / "planning guess: not measured at 45 s". No 61 s or 62 s planning figure is live text (CT 64 and 118 only describe the old figures as reasons). |
| 12 | CT 216 row 36 | replacement cell now "one Postgres server with two databases (n8n's own and the take's)". The quoted original sentence stays in its quote column (it is the file text being replaced). The apostrophes are the lead's wording and the paste checker passes. |
| 13 | CT 9 | run list no longer promised empty (same as RW 72). |
| 17 | RW 63, 201 | A-057 released on the Q16 psql four-column check, not F-001 (dropped). |
| 18 | RW A-073b, A-076a, A-076b (204, 210, 211) | replacement DELETE, marked CUT with old note kept. |
| 19 | CT 182, 201, 212, 213, 222 | first mention of OWNER-STEPS-realrun-v3.md now says v4 replaces v3 (decision 10; v3 archived, never deleted). CT lines 35, 59, 80-83, 96, 114, 139, 161, 471, 475, 743, 804, 808 also name v3 and were NOT changed (not in the finding's list, not table rows); they are history or instructions. |

## Raw RESULT lines
check_patches.sh (run from /home/user/hadavin-sdk): `PASS 4 patches` (earlier resolve-007-r1 said 5 patches: F-001 was dropped since; the count is not a regression).
check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md: `total rows: 158` / `RESULT: PASS`
claims-count.py CLAIMS-TABLE.md: `total 327`, `to-do rows: 87`, `offenders: 0 []`, `ids: 327 unique: 327`
Counts unchanged, so no stated count was edited.

## Not fixed (others own the files)
Items 1-4, 6, 7, 9, 14-16, 20-22, 24 touch EXCEPTIONS, FINDINGS, FIX-PLAN, QUEUE, REPORT, CUT-LIST, OWNER-STEPS, fill_flows: owners must apply them. Item 24 (Python 3.10+ vs 3.11+): flow-check/README says 3.10; I did not change it because I did not verify which one fill_flows/README states. Nothing ran in n8n.
