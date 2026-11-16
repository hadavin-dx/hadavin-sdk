# Fix log: RUNBOOK.md, readers r66 (370-509) and r67 (220-370)

Static fixer. Only RUNBOOK.md and this log were edited. Backup before the edits: `/tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/RUNBOOK.before67`. RUNBOOK.md is now 528 lines (was 509); line numbers cited by the reports and by QUESTIONS.md have moved. Every new command is untested static text. No decision, default, rating or time set by a lead order was changed. `pass-words.sh` was not edited.

Read first (not verified by me):
- The count `grep -c '^| I'` is 68 both in the backup and now. The brief says 67. I did not add or remove I-rows (new decision-table rows start with "| Open question"). The difference is from before my work.
- No test was run on any new command; only the static checks below.
- Where no file holds a value, the cell says "LEAD DECIDES: owner, due HH:MMZ (HH:MM IST)" with values copied from existing files.

## Report r66 (reviews/runbook-reader-r66-370-509.md)
| Finding | Status | Where / reason |
|---|---|---|
| B1 I24 table vs row | fixed | decision table row I24 now names the four shas and Tue 04:26Z (09:56 IST), like section 10 row I24 |
| B2 NO-GO deadline 06:53Z vs table | fixed | one reading: 06:39Z operator target with the control, 06:53Z only if I30b is no; table, N5 and the commentary say the same |
| M3 "I30" three questions | fixed | split into I30a (meaning of the 23 Nov limit), I30b (control in the repeat) and the rule-conflict row; each has an owner and a due time |
| M4 missing table rows | fixed | rows added for I25, I27, I42, I44, I45, I47(b), I4, step 6, the control, the hook leg, the W-Tue move, step 17 length, step 9 |
| M5 conflicting due times | fixed | I14, I16, I31, I41, I43, I45, I46 aligned to section 10 rows; one answer-by per input, stated before the table |
| M6 WAIT_S two times | fixed | one answer-by, matching rows I54/I55 and the TAKE-CHECKLIST alignment |
| M7 I33 table vs row | fixed | table row says step 6 copies the two Tuesday scripts at 04:54Z, the rest due 09:00Z |
| M8 same input two ids | fixed | I47(a)/I57 and I58/I33 cross-referenced as one input with one time |
| M9 "owner" two meanings | fixed | "owner" = studio owner, supplier named separately; supplier wording changed in section 10 |
| M10 N1-N7 no clock times or words | partly | N1 times, N2/N3/N6 deadlines and saved words added where files give values; N3 EGM review time and some N-step printed words stay LEAD DECIDES because no file holds a value |
| M11 T3 no printed word | fixed | T3/T4 name the log and the exact pass words |
| M12 broken "M7" references | fixed | section 10 now has a labelled M7 paragraph; references point to it |
| M13 dependencies without deadline | partly | rounds 23/24 merge, and other dependencies got owner and time from existing files; the remainder is LEAD DECIDES with a time |
| M14 line 403 too long | partly | instruction and commentary separated, "GOVERNING NOW" removed, times unified; the paragraph is still long because the numbers it carries are needed |

## Report r67 (reviews/runbook-reader-r67-220-370.md)
| Finding | Status | Where / reason |
|---|---|---|
| B1 step 15 cannot pass (RC4 due 09:00Z) | fixed | RC4 excluded in step 15 and the section 7 RC4 row, with its own time |
| B2 step 26 pass line | fixed | step 26 names the command that writes `$POSTLOG.counts` / `.mail` / `.mail2` (untested static text); `pass-words.sh` not changed |
| M3 step 6 vs I33 | fixed | two files at 04:54Z, others later; pass cell lists start-syntax-ok, syntax ok, control exit 0, grep exit 1 |
| M4 re-smoke length | fixed | 74 minutes with the control, ends about 09:43Z (15:13 IST); 60 minutes without; marked LEAD DECIDES (I14, I30b) |
| M5 rehearsal 1 time | fixed | 07:44Z (13:14 IST) with the dated 07:40Z noted; Z suffix added to table times |
| M6 missing rows | fixed | I44, hook leg, W-Tue move added |
| M7 WARN reader time | fixed | 04:26Z for 4b stated; step 13 "again" given 07:14Z |
| M8 step 14 (d)(e)(f) | fixed | printed words by `stepjudge` lines; I34/I35 got owner and time |
| M9 steps 21, 23 | fixed | pass words added; rule d/e and scene-4 wording unified |
| M10 owner's edited video check | fixed | check before post added in steps 28/30 with I27 time |
| M11 step 27 "LEAD FILLS" | fixed | pass words written out |
| M12 step 17 GO/NO-GO line | fixed | saved line via `stepjudge` and a read-back without a pipe; length question put to the lead (no order gives a number) |
| M13 step 9 credentials | fixed | owner, time 05:54Z and outcome (stays BLOCKED, NO-GO at step 17) |
| M14 step 18 60 vs 64 min | fixed | 64 minutes with the fourth gate, as an AUDIT PROPOSAL with a lead question |
| M15 step 8 | fixed | failure action added |
| M16 step 4 | fixed | failure action added |
| M17 BLOCKED-by cells | partly | a paragraph "How to read a BLOCKED-by cell" now sends the reader to the section 10 row for owner and time; the cells themselves still show I-numbers only (changing every cell risks the 9-cell table and the I-row guards) |

## Checks run after the last edit (last line of each)
- `grep -c '^| I' RUNBOOK.md`: 68
- check_refs: PASS 5190 references
- check_names: PASS 655 rows
- check_secrets: PASS 0 hits in 3022 files
- check_counts: PASS 52 files / 655 nodes
- `ruff format --check .`: 1147 files already formatted
- check_runsheet_paste: RESULT: PASS
- Step table rows between lines 255 and 320 were rechecked for 9 cells after I fixed one row (step 17) that had a stray pipe; I did not recheck rows outside that range by cell count.
