# fix-rwct23: read r22 (reviews/rw-ct-reader-r22.md), round 23, non-security. One fixer. Static; nothing run; made-up data.
Files edited: RUNSHEET-WORDING.md (RW), CLAIMS-TABLE.md (CT), this file. No status changed, no row added: RW 195 rows (PASTE 53, DELETE 30, HELD 89, NO PASTE 9, SUPERSEDED 14), CT 330 claim ids unchanged. Paste strings changed (RW and CT together, pairs check 140 of 140): N-5a, N-10, N-11b, A-087a, A-008a, B-195, B-197, B-010.

## Failures and uncertainty first
- Not fixed, by design: the declared Blocker (nobody named to speak, hold the capture, empty the mailbox). It is a lead question (Q31 item 100 / RWQ-10). RW now says it ONCE and clearly in a new bullet at the top of "Read first"; the older mentions stay as short pointers.
- N-5a lane row: contested in part. I did NOT add a counted CT row (it would change 330, the pairing rule and every total for a sentence that is not a file sentence). Instead CT now carries a verdict line for N-5a (lease 45 s SUPPORTED via A-055; takeover is by the separate recovery flow; stop and restart on purpose is the plan of step 13, not an observation). If the lead wants a counted row, say so.
- Line 3 shape example "lead-one 2026-11-17 08:20Z" has no IST on purpose (it shows what is typed in the blank, which is UTC only).
- Still unverified by me: all flow, script and ORDERS facts (static audit; reviewer cites located by text, none contested except as noted). Round 22 reviewer did not read RW 1-85 etc.; I did not re-read those parts beyond the lines I touched.
- The 07:00Z latest re-pin margin still has no reason in any file (said so, unchanged: lead question).

## Finding -> result
1 N-5a: fixed. New string says we stop n8n on purpose and start it again, explains n8n, flow, lead before use, says a SECOND FLOW (recovery flow) takes over, not a second copy; number 30 still out. RW note and CT bullet updated; CT intro says N-5a has a verdict line.
2 Speed-up: fixed per class. One rule in RW row (u) and step 13: no part of the video is sped up unless the words sped up are on screen for that part; default nothing sped up, scene 4 cut. N-10 string adds the rule, N-11b string now "then cuts, or speeds up only with the words sped up on screen", A-087a drops "the sped-up cut" (RW and CT lane row A-087 and Table 1 row 3 in step). Left unchanged on purpose: the quoted OLD sentence of A-087a/c/d and the rows of section 7.
3 A-008a: fixed. "Scenes 1 to 4:" dropped from the string (RW note records it; CT WL-11 now says DECIDED; CT A-008 and Table 1 row 4 strings updated). A-008b (later video) keeps its own words.
4 B-195, B-197: fixed. Both strings now end with "reported by another test session; we have not seen its raw files" (RW, CT lane rows and Table 2 rows 72 and 74). Sibling scan of every paste string with counts or times: all other relayed strings already carry the words.
5 CT delete request 1: fixed. CT lines for owner definition and Step D now say steps 2c, 3, 4 and 6 and name the practice run (two places; RW unchanged, it wins).
6 Stale counts: fixed. CT now says PASTE 53, DELETE 30, HELD 89, NO PASTE 9, SUPERSEDED 14 (195); A-083 wait is A-073a only in both CT places; row 33d is B-215 (was B-214).
7 Order: fixed. RW section 0c intro now writes the real order once (F-008 decision, step 1b items 1 to 3, item 4, re-pin written done, import, then 2a onward) and drops "no step waits for a later step" as an unqualified claim; step 2 repeats the order in short. The import-after-re-pin placement is read from step 2 ("only then runs step 1b") and is lead to confirm.
8 B-010: fixed. String now "as the flow is built ... built to share ... built to replace", and "has not been observed on the real CRM service" (RW, CT row 46 and lane row; note cites B-009).
9 S9-2, S9-3, challenge number: glossed at RW owner definition (first use) and at the Step D line.

## Lower items (same pass)
- UTC without IST: class fixed by script on both files (26 in RW, 34 in CT, covering RW 90, 171, 438, CT 20, 85-87, 191, 303 and siblings); a second scan finds only the line-3 shape example and one line that already has IST before the UTC time.
- RW 90 "four hours": now four durations adding to 4.5 hours, stated as a lower bound that leaves out steps 1b, 2, 2a, 2b, 4, 5, 7 to 9 and the owner delete wait; "no file gives its reason" now says ORDERS item 7 gives only the latest slip of the take (12:00Z = 17:30 IST), a different time.
- RW step 2a: send list now includes 2c; no start command for fake_model_server.py stated plainly (demo-only file, not in this checkout).
- RW 7a: heading and L-9.1 and one past-error line say test programs (two stand-ins plus the stage service, which is not a stand-in by the RW definition).
- CT B-062: paste string cited as RW row B-062; V-11 string kept as its own R:11 sentence.
- CT Table 2 row 42: Total 20 string kept, with the default-path 19 stated beside it.
- CT B-032 note: the 59.6 s figure now carries the relayed words. CT B-127: no longer says the owner decided; F-008 is proposed, lead decides. CT B-077: "owner" replaced by the person who receives the alerts. CT Q22 item 3: line 135.

## Proposed Q31 items (a Q31 fixer owns QUESTIONS.md; no lead answer invented)
- Q31-new-A: Who starts Postgres, n8n, the stage service, the fake model program and the stand-ins before the first send, and where are the start commands written? (RW step 2a; needed before step 2a.)
- Q31-new-B: Are any parts of the video sped up? Default if no answer: no, nothing sped up, scene 4 is cut (RW input-table row (u)).
- Q31-new-C: By what time does the studio owner delete the contacts of delete request 1? (row (v)).
- Q31-new-D: In which scene or step does the studio owner type y, the challenge number and end on camera? (line of the owner definition).
- Q31-new-E: Does the closing card exist (Q-F), answer by when? And is the re-pin date and hour set before rehearsal 1 (Q-H)?

## Commands (run from handover/flows-audit, raw tails)
python3 -I tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md -> total rows: 195 ... RESULT: PASS
python3 -I tools/check_rw_ct_pairs.py ... -> paste strings in RW: 140 | found word for word in CT: 140 | not found in CT: 0
python3 claims-count.py CLAIMS-TABLE.md -> total 330; lanes A 100, B 226 incl. X; to-do rows 87; offenders 0; ids 330 unique
python3 -I tools/check_refs.py -> PASS 5171 references
python3 -I tools/check_names.py -> PASS 655 rows
python3 -I tools/check_secrets.py -> PASS 0 hits in 2681 files
ruff format --check . -> 829 files already formatted
