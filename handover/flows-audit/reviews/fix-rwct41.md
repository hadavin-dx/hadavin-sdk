# fix-rwct41: RW / CT round 41 fixer (inputs: reviews/rw-reader-r41.md M1 to M14, reviews/ct-reader-r41.md M1 to M3)

Files edited: RUNSHEET-WORDING.md (RW) and CLAIMS-TABLE.md (CT) only. Nothing committed. fix-rwct40 not undone. EGM skipped for the checking of reviewer words: non-security fix pass beyond round 2, run by the lead's order. Static work only; nothing ran in n8n.

## RW (reviewer words checked by text; where wrong, said)
- M1 real. The wait "until the table screen has been run once in n8n" (A-092, A-097a, A-097b, N-2, A-043) is now "until the rehearsal screenshot or the one-time preview exists (step L-9.6 of section 7b)"; the strings that say "was not run" stay true.
- M2 real. A-083 and A-083b notes: A-073c pasted without A-073a writes a new statement 17, so the total is 19 only when A-073b is applied and neither A-073a nor A-073c is pasted; 20 otherwise. The same rule is now in the CT rows 42 and A-083.
- M3 real. A-098 string: "was not observed in this test" is now "was not observed" (RW and CT, same string).
- M4 real, partly: "check" now says what it is: "no later pass of the recovery check (the part of the flow that looks for stuck leads and runs over and over)". I did not use the reviewer's "30 s check": CT reader notes say the real-v4/v5 timer is 45 s, so no number is given.
- M5 real. B-165: the 720 s hold and the 60 s waits are now two sentences, with "how these tries fit inside the 720 s hold is not confirmed".
- M6 real. B-156: "meant to be longer than a normal run ... the real CRM step and the mail step have no time limit of their own in the flow files, so this is not guaranteed".
- M7 real. "(off by default; read in its code, not observed)" now says "reported by a trace file of the desk code, reviews-f1/trace-desk-repo.md, because the desk code is not in this checkout" in all 8 RW places (B-067, B-091, B-213, B-215, B-215b and the others with the same text) and all 12 CT places. The trace file does name the cleanup option (B-068 line).
- M8 real. B-189 and B-183 strings now carry "as stated by the lead; the desk code is not in this checkout, so not checked here"; "the portal" is marked "a part of the desk that no file we read describes". Both stay PASTE (no status count moved).
- M9 real. B-003d note preview now equals the string word for word.
- M10 real. B-010 string: "the recording is planned to use ... (not checked: the take script is absent)" (RW and CT).
- M11 and M12 real. Section 7b reordered: L-9.3 deactivate, L-9.4 read the lead table, L-9.5 activate, L-9.6 the screenshot step that was L-1 (now after activation), L-9.7 restart capture. All references to L-1 changed to L-9.6 (only RW had any); N-8 note says L-9.1 to L-9.7.
- M13 real. A-010, A-010b, A-010c (and CT paste copy): "The lead table has other columns (not among the six shown on screen) that can hold the made-up name and e-mail address, and the files we read set no expiry for them."
- M14 real. The spoken hedge "(read from the flow, not yet run)" is out of the strings of A-021, A-030, A-033a, A-033b, A-035, A-039 (RW and CT) and replaced by "is built to"; the hedge sits in each row's note; A-033a note names the test program smtp_catcher.py.

## CT
- M1 real. CT lane A count block now UNSUPPORTED 3, OVERSTATED 43, UNTRACED 10 (hand tally by script of the lane A rows: SUPPORTED 21, RELAYED-ONLY 23, OVERSTATED 43, UNSUPPORTED 3, UNTRACED 10 = 100). Part 7 table now 64 / 41 / 7 / 47 / 71 = 230, equal to line 122. I also fixed a stale "89 SUPPORTED claims, 16 ... other 73" at CT line 127 to 85 and 69 (same as line 170).
- M2: regraded A-004 UNTRACED to OVERSTATED (stage_server.py exists; lines 11 and 16 wrap LiveQualifier; its RW row A-004 exists). NOT regraded: A-014, A-018, A-037, A-022 (reviewer right on the definitions: files exist and partly check) because each has no RW row and tools/check_runsheet_paste.py would FAIL (proved on a copy for A-089).
- M3: A-089 NOT regraded for the same reason (the reviewer is right by the first-phrase rule). All five are listed in the CT bullet "Open regrades left to the lead", item (e), with the totals they would give (SUPPORTED 84, OVERSTATED 95, UNTRACED 77) and the need for one new RW row each. The 622(a)-style list is the place.
- Minor: A-060 quote now opens with its first clause; A-072 now says the version 2.46.6 is also at P:115 and P:148.
- Counts repeated and updated: CT lines 15, 116 (rowless 84, 63, 68, 18 and "eighteen" with A-004), 121, 122 (lane split 43 and 10), 127, 170 (100 = 90 + 10, minus 18 = 82, plus 15 = 97; 97 flagged and 80 UNTRACED for the checker), 217 (lane A UNTRACED now 10), 617-618, the Open regrades totals, Part 7. RW: line 33, History line, "Not reviewed" bullet, line 483, A-004 mentions.

## Counts
Before: SUPPORTED 85, RELAYED-ONLY 64, OVERSTATED 89, UNSUPPORTED 10, UNTRACED 82 = 330 (lane A 21/23/42/3/11; B+X 64/41/47/7/71).
After: SUPPORTED 85, RELAYED-ONLY 64, OVERSTATED 90, UNSUPPORTED 10, UNTRACED 81 = 330 (lane A 21/23/43/3/10). 330 ids unique; RW rows 199; 144 paste strings found word for word in CT.

## Raw last lines
- claims-count: `verdicts: {'UNSUPPORTED': 10, 'OVERSTATED': 90, 'SUPPORTED': 85, 'RELAYED-ONLY': 64, 'UNTRACED': 81} total 330` / `offenders: 0 []` / `ids: 330 unique: 330`
- check_rw_ct_pairs: `paste strings in RW: 144 | found word for word in CT: 144` / `not found in CT: 0`
- check_runsheet_paste: `claim ids marked UNSUPPORTED, OVERSTATED, DELETE or STALE ...: 97 | with no row here: []` / `claim ids marked UNTRACED there: 80 | with no row here: 68` / `RESULT: PASS`
- check_refs: `PASS 5192 references`; check_names: `PASS 655 rows`; check_secrets: `PASS 0 hits in 2851 files`; check_counts: `PASS 52 files / 655 nodes`; ruff format --check .: `976 files already formatted`

## Not fixed
- Regrades of A-014, A-018, A-022, A-037 (to OVERSTATED) and A-089 (to OVERSTATED): need a new RW row each; lead choice (listed in CT).
- Not checked: whether any desk string is true (desk repo absent); RUNBOOK.md and QUESTIONS.md untouched, so any mention there of RW step L-1 (none found by grep of QUESTIONS.md, RUNBOOK.md, README.md) or of the old counts was not changed.
