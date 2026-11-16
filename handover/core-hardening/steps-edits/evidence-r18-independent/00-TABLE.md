# EVIDENCE RUNNER table, EDITS r18 (independent). I run and record; I do not judge.
Started 19:21 UTC = 00:51 IST (Tue 17 Nov). Finished about 19:45 UTC = 01:15 IST. Folder: this one. Builder files copied, never edited; the builder's input files were copied too (a tree `h/core-hardening/{inputs,steps-edits}` plus `tests/`), because verify18.py finds its inputs from its own location.

| # | Command (all `python3 -I`) | Exit | Time (UTC) / load | Raw output | Result |
|---|---|---|---|---|---|
| 1 | `NO_NEG=1 verify18.py` (own copy) | 0 | 19:22, load 1.5 | run-noneg.txt | FAILURES 0; plants occurrence 167/167, pair 71/71, reversal 10/10, day sheet 10/10, appendix 9/9; r18 section 102 checks |
| 2 | full `verify18.py` with 198 negative controls, through `heavy-slot.sh` | 0 | slot 1 taken 19:27:36 (wait about 6 min), ended 19:41:28, load 2.4 to 3.6 | run-full.txt, run-full.exit, heavy.log | FAILURES 0; 198 NEG caught, 0 "NOT CAUGHT" |
| 3 | `EDITS_PATH=EDITS.round17.md NO_NEG=1 verify18.py` | 1 | 19:35 | run-on-r17.txt | 113 FAIL lines (86 r18, 18 r17, 9 older): matches the builder claim |
| 4 | my own 24 mutations (`mut.py`) | n/a | 19:29 to 19:31 | mut-results.txt | 18 caught, 6 missed (see below) |
| 5 | own UTC/IST pair + weekday scan (`my-pairs.py`, inline) | 0 | 19:25 | in report | applied sheet 71 UTC times, day sheet 17, appendix 6: 0 wrong pairs, 0 wrong weekdays (3 seconds-form times checked by hand: 18:01:00 to 23:31:00, 18:15:20 to 23:45:20, 18:14:40 to 23:44:40, all right) |
| 6 | banned strings (tuple read at run time by `ast` from tests/test_no_reference_material.py, 10 entries) + key-shape scan (`scan.py`) | 0 | 19:27 | in report | banned hits 0 in all 8 files; key-shape counts 0 for every key shape; only 14 (EDITS.md) / 8 (applied sheet) e-mail shapes, all at the reserved example domain |

## Word counts (my method)
Method A: `wc -w` of the applied copy `scratch18/scratch-apply11/OWNER-STEPS-realrun-v3.md` (Apply-now rows applied to a copy of the input): 21,492. Method B: Python `len(text.split())` same file: 21,492. Method C (words that start with a letter or digit, trimmed of symbols): 21,325. Day sheet: wc 2,020 (C: 1,920). Appendix K file: wc 1,272, and it equals the section in EDITS.md byte for byte after strip. Input OWNER-STEPS: 4,488 words. All builder numbers confirmed.

## Other builder claims re-checked
60 rows (48 Apply now, 12 Hold): confirmed by verify18 output. EDITS.md "1087 lines": `wc -l` says 1086 (1087 if the missing final newline is counted as a line; trivial).

## My 24 mutations (each on a private copy; NO_NEG=1 run of the builder's verify18.py; "caught" = at least one FAIL line)
| Id | Mutation | Files changed | Result |
|---|---|---|---|
| M01 | 18:19 UTC paired with 23:39 IST (one copy) | EDITS | CAUGHT (r13 time arithmetic) |
| M02 | day sheet alarm 3 becomes 18:19 UTC = 23:39 IST | day sheet | CAUGHT (count) |
| M03 | alarm 3 pair 18:09 = 23:49 in every copy | EDITS+day | CAUGHT |
| M04 | "Last day, Tue 23 Nov 2026" in every copy | EDITS+day | CAUGHT (weekday) |
| M05 | delete "Shredding does not revoke the key..." everywhere | EDITS+day | CAUGHT |
| M06 | new keys first "always" (reversed default) everywhere | EDITS+day | CAUGHT |
| M07 | remove "read the list of what the assistant will remove" step everywhere | EDITS+day | CAUGHT |
| M08 | typed word `please stop looking` renamed everywhere | EDITS+day | CAUGHT |
| M09 | duplicate row E-20 | EDITS | CAUGHT (rows != 60) |
| M10 | first "Tue 24 Nov 2026" moved to "Mon 23 Nov 2026" (it is in the lead-confirmation text, EDITS.md line 87) | EDITS | MISSED |
| M11 | forged counts in r18-CHANGES.md (21,492 to 20,492; 198 to 199) | CHANGES | MISSED (verify18 never reads CHANGES) |
| M12 | row E-04 status Hold changed to Apply now | EDITS | CAUGHT |
| M13 | seconds pair 18:15:20 = 23:55:20 | EDITS | CAUGHT |
| M14 | alarm 1 loses its IST pair everywhere | EDITS+day | CAUGHT |
| M15 | `key revoked` reply "answers it once" changed to "never answers it", in every copy | EDITS+day | MISSED |
| M16 | "Wed 18 Nov 2026" changed to "Thu 18 Nov 2026" | EDITS | CAUGHT |
| M17 | delete 2nd sentence of K-A (it holds a time pair) | EDITS+appendix | CAUGHT (by the pair count) |
| M18 | delete "The assistant never opens the files." everywhere | EDITS+day | MISSED |
| M19 | swap card steps 2 and 3 in the day sheet only | day sheet | CAUGHT |
| M20 | appendix 18:29 UTC = 00:29 IST | appendix | CAUGHT |
| M21 | "only 10 minutes" changed to 20 everywhere | EDITS+day | CAUGHT |
| M22 | delete 2nd sentence of K-D (no time inside) | EDITS+appendix | MISSED |
| M23 | delete "(never its content)" everywhere | EDITS+day | MISSED |
| M24 | reversed default: if neither shred word is written, treated as `shred done` | EDITS+day | CAUGHT |

Pattern of the 6 misses: the checker pins safety wording by an exact list of phrases (32 in `_CANON18`) plus older per-row phrase checks; a safety sentence that is not on those lists, changed or deleted in ALL copies consistently, passes (M15, M18, M22, M23); the lead-facing text is not pair/date-checked for the 24 Nov date (M10); and the CHANGES file numbers are not checked at all (M11).
