# Fix log rwct17 (fixer for reviews/rw-ct-reader-r10.md). Static work only, nothing committed.

## Not verified (first)
- Nothing ran in n8n, a database or a mail service. All changes are wording and ordering in two files.
- The Q31 answer-by times in the step 1a table were copied from QUESTIONS.md and not checked independently.
- Unknown: whether a second send of the same lead ID makes a model call. Step 2a therefore counts five sends (P4a 1, rehearsal 2, take 2) and invents no cap number: "cap set by Q31 item 3, lead to confirm".
- M12: I re-read only the cited spots of CLAIMS-TABLE.md after editing, not the whole file.
- M10: the words wait, table row, owner, take, label, lead were swept only in section 0, section 0c and the "table row" cells, not through all of section 7.
- The reviewer's words are unverified. Cited lines were re-read; they matched (RW 137, 138, 140, 167, 410). Two points were partly wrong: B-016 and B-019 are one sentence per cell (cell splits), not a two-string violation; B-024's slashes separate five cells and are not typed. RW 136 vs 398 disagreed only on "coordinating session"; both now say "the lead".

## Fixes (files: RUNSHEET-WORDING.md = RW, CLAIMS-TABLE.md = CT)
- B1: new steps 12a (the wait, mailbox pane after the wait, mf_leads row in frame, count written before lead ID 2 is sent) and 13a (recount by lead ID 1 after scene 4, same count, exactly 1, not filmed). Steps 10-13 carry the P4a filming condition.
- B2: new step 2a, model-cost check before the first send; step 3 waits for it. Send count stated honestly; no cap invented.
- B3: step 1a table (a)-(k), 3 columns (the paste checker treats 4 or 6 cell tables as paste rows). Inputs without a Q31 item are written "UNANSWERED": (d) P4a send command, (e) hadavin_label check, (f) Gmail filter.
- B4: "Who acts" default in 0c (lead is presenter and typist until named); steps 10-13 tagged; APPROVED blank shape defined at the top of RW: `APPROVED: <session name> <YYYY-MM-DD> <HH:MM>Z`. RWQ-10 and the line "who the presenter is" now point at the default.
- M5: APPROVED marks moved into step 8; the four extra example.test swaps (R:31, R:55, R:68, R:87 header) are written there.
- M6: step 7 prepares two lead IDs (ID 1 for scenes 2-3, ID 2 for scene 4).
- M7: one cut limit (3 minutes unless the lead writes another); one wait floor (more than 75 s plus a lead margin).
- M8: new paragraph "Voice rows and the one result" in 0b; only the scoped sentence A-016f is spoken as the result; A-001 applies only after P4a passes.
- M9: exemption list extended (A-087b, A-096, B-092, B-100, B-145, B-147, B-151, B-153, B-173, B-173b).
- M10: "coordinating session" became "the lead"; "plan table row" and "file table row" separated.
- M11: "step 5" became "step 10" (RW line 167).
- M12 (CT): stale line numbers removed; WL-14 time corrected (07:00 UTC = 12:30 IST); D1/D2 aligned with RW; rows 2 and 5 say "Status in RW: HELD"; row 3 points at A-087a/b; row 4 wording fixed.

## Pointers in other files
Sub-steps 2a, 12a, 13a were added; no step was renumbered. No pointer in README, REPORT, STATUS, FIX-PLAN, TAKE-CHECKLIST or OWNER-STEPS needed changing. Counts unchanged (195 rows, 55/30/87/9/14; CT 330) because no row status or paste string changed.

## Files I must not edit that need a change (for the lead)
QUESTIONS.md: add Q31 items for the P4a send command, the hadavin_label check, the Gmail filter and label demo, and the second lead ID.

## Checker output (after the last edit)
- check_rw_ct_pairs: 140 found word for word, 0 not found.
- check_runsheet_paste: RESULT: PASS.
- claims-count: 330 ids, 330 unique.
- check_refs PASS 5176; check_names PASS 655; check_secrets PASS 0 hits in 2022 files.
- ruff format --check: 736 files already formatted.
