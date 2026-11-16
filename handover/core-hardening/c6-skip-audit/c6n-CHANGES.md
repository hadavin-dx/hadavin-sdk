# c6n changes (what changed from REPORT-c6m.md, per review finding)
Stamp: 2026-11-16T15:27:47Z (IST = UTC+5:30). Status of the report: NOT APPLIED. 72 rows, 35 ready, 34 on defaults only, 3 with a check (rows 23, 58, 59).
Detail of each row is in REPORT-c6n.md; the full list with section numbers is its section 8.

## Naive review of c6m
- B1: the action box is rewritten in plain words: seven-point preface, table of every L- and C- label, one answer line the studio lead can type exactly, does / does NOT / still-to-do lists, earliest realistic date, how to reverse a default (evidence-c6n/box_c6n.md).
- M1 to M8: the glossary and box now explain re-pin, risks list, rehearsal list, hiding versus automatic removal, the timing number, ready, and the two roles (studio lead, owner). Bare "lead" replaced by "contact" or "studio lead" in all new texts. Gate lists (risks list, rehearsal list) named and separated; the contact-deletion search sits only in row 8. Stop rules added as table 3e. Rows 3 and 4 now depend on L-CARD, L-CARDCUT, L-CARDTEXT. Rows 58 and 59 depend on C-8 only.
- m1 to m9 and the "could not follow" items: each fixed by wording changes in sections 0 to 5 and rows 1, 3, 4, 6, 8, 9, 11, 13, 14, 17, 21 to 24, 37, 40, 41, 44, 48 to 50, 54, 58, 59, 62 to 69. Table 3b and the "rows tied" column are regenerated from the parsed rows.

## Design review of c6m
- M1: the 45 s lease is counted from the first send (claim row written, mf-form.json:97), not from the first reply. Rows 6 and 21 give the gap rule: under 30 s from the first send, 15 s margin; scene 2 (40 s budget) must be shortened or the first send made late in it.
- M2: "two stores" removed. stage.journal is a third record. No viewer-facing sentence on the number of stores until C-8 passes; then only "one Postgres server, two databases". L-ONEDB is tied to no row.
- m3 to m9: both voided runs (VOID-fl45k3b, VOID-fl45k6c) named wherever kept runs are counted (report lines 52, 54, 113, 449 and the section 8 line); retention wording no longer assumes automatic removal of old runs; rows 40 and 48 name the branch cloud/core-hardening; L-SAVE no longer quotes "owner 2026-11-16".

## New in c6n
- Closing card spoken length: 144 words, about 58 s at 150 words a minute, against a 30 s budget; the old card held about 155 words; total video about 208 s if all read aloud. Disclosed in section 0 and section 9 as needs-lead (stopwatch run). I did not cut spoken text.

## Not changed
- Verified-sound parts of c6m are copied unchanged.
