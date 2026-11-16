# fix-rwct42: RW / CT round 42 fixer (input: reviews/rwct-reader-r42.md; reviews/fix-rwct41.md section "Not fixed")

Files edited: RUNSHEET-WORDING.md (RW), CLAIMS-TABLE.md (CT), this report and reviews/checkpoint-rwct42.md. Nothing committed. Static work; nothing ran. EGM skipped for checking reviewer words: non-security fix pass beyond round 2, by the lead's order.

## What I did not do or could not check (first)
- Reviewer r42 did not read RW 56-204, 515-574 or CT 153-482 and other gaps; I did not read them either except by script. No desk-repository cite was checked (desk repo absent).
- The new HELD rows hold no string, so no reviewer has read them yet; they are not read by any stranger read.
- Nothing contested: all five Majors and the smaller points checked true against the files.

## Findings
- M1 B-174 real. CT verdict now OVERSTATED (first half read in the flow, "The take treats it as not has_crm" has no file; second verdict not counted: SUPPORTED/UNTRACED split) with safe wording. New RW row B-174 (NO PASTE, no string).
- M2 B-162 real (AlertFailed absent from the real-v5 files; exists only in the older n8n-flows-real). CT now OVERSTATED with safe wording naming AlertClaim, AlertMark, AlertBackoff. New RW row B-162 (NO PASTE).
- M3 B-017 real. CT note now: "is said, in a trace file we did not re-read (reviews-f1/trace-desk-repo.md), to describe the old desk harness; not checked here".
- M4 B-130 real. Regraded UNSUPPORTED to OVERSTATED (second verdict, not counted: SUPPORTED ONLY BY RELAYED NUMBER); note reworded "on the lead's report only"; to-do row 59 and its list line updated. The RW row B-130 and its paste string are unchanged (it already says "as reported by another test session"), so the 144 pairs hold.
- M5 B-213 real. First sentence of the string now: "contacts are built to appear in the real CRM, and up to one e-mail message per person is built to appear in the Gmail label named demo (read in the flow files, not observed)." Same text in RW and in CT (to-do row 32 string); CT row B-213 prose aligned.
- Smaller: B-156 CT safe wording now says "whether that can send a second e-mail message is not measured" (as RW); B-150 data cell now points to B-165 and the alert nodes (B-155 is the lease row); B-198 to B-200 CT notes say "NOT REPRODUCED" is the file's own statement, relayed; RW B-198..B-200 note "Claims table says DELETE" reworded to "grades it OVERSTATED; this row deletes it" (B-093 left as is: it is UNSUPPORTED). I could not reproduce what "left alone" meant exactly in the reviewer's note; I treated it as the relayed-basis wording.

## The five regrades (A-014, A-018, A-022, A-037, A-089)
Confirmed by reading the CT rows and the run sheet lines R:24, R:32, R:33, R:38, R:39: the flow path or one of two files is read, the outcome or one half is not proven, so OVERSTATED by the CT definitions and the first-phrase rule. Each got one new RW row, status HELD, Paste cell NO PASTE (marker edit only: old sentence not filmed, spoken or shown, rule HELD). No string was added, so the 144-pairs check cannot break; PASTE count stays 55. Placed in section 1 (A-014, A-018, A-022) and section 7 (A-037, A-089).

## Counts (all updated in RW and CT: lines for verdicts, lane splits, flagged, UNTRACED, rowless 233, status table, section counts, Open regrades bullet, Part 7 table, lane A block)
Before: 85 / 64 / 90 / 10 / 81. After: SUPPORTED 82, RELAYED-ONLY 64, OVERSTATED 98, UNSUPPORTED 9, UNTRACED 77 = 330. Lane A 20 / 23 / 48 / 3 / 6 = 100; lane B+X 62 / 41 / 50 / 6 / 71 = 230. Flagged (A and B ids) 104; UNTRACED A and B 76, 64 without row. Rowless claims: 81 SUPPORTED, 63 RELAYED, 64 UNTRACED, 25 OVERSTATED = 233 (by script). RW status table: PASTE 55, DELETE 30, HELD 96, NO PASTE 11, SUPERSEDED 14 = 206 rows (sections 59 / 21 / 78 / 48); I checked the table against the row statuses by script (matches).

## Verification, last lines
- claims-count: `verdicts: {'UNSUPPORTED': 9, 'OVERSTATED': 98, 'SUPPORTED': 82, 'RELAYED-ONLY': 64, 'UNTRACED': 77} total 330` / `offenders: 0 []` / `ids: 330 unique: 330`
- check_rw_ct_pairs: `paste strings in RW: 144 | found word for word in CT: 144` / `not found in CT: 0`
- check_runsheet_paste: `...: 104 | with no row here: []` / `claim ids marked UNTRACED there: 76 | with no row here: 64` / `RESULT: PASS`
- check_refs `PASS 5193 references`; check_names `PASS 655 rows`; check_secrets `PASS 0 hits in 2863 files`; check_counts `PASS 52 files / 655 nodes`; ruff format --check . `988 files already formatted`.

## Lead decisions needed
- B-162 and B-174 got NO PASTE rows (their sentences sit in design and README files, not in the video). If the lead wants corrected text pasted into those files, a PASTE string must be added to both RW and CT.
- RUNBOOK.md, QUESTIONS.md, TAKE-CHECKLIST.md, FIX-PLAN.md not touched, so any count there (85/64/90/10/81, 199 rows, 97 flagged) is stale until the lead sweeps them.
