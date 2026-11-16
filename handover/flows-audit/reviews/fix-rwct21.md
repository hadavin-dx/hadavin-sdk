# fix-rwct21: fixes for rw-ct-reader-r14.md (12 Majors), RW and CT edited together
Static work only: nothing run in n8n, Postgres, HubSpot; no network; no secret printed. EGM skipped: the lead runs the EGM result review (this fixer cannot invoke the egm agents). Reviewer words were unverified; each Major was checked against the files first. No Major was wrong; M-3 and M-9 were right in substance (details below).
Not done / uncertain (first): (1) the new strings were not read by a fresh reader; (2) M-4, M-7 and delete request timing are not decided by any file, so they are UNANSWERED (the lead adds Q31 items; QUESTIONS.md is not my file); (3) blocked inputs unchanged: no named performer for scenes 1 to 4 (row (o)), missing send command of P4a (row (d)).
Counts unchanged: RW 195 rows, CT 330 ids (lane A 100 + Part 7 230). Rows (u) and (v) are input-table rows (3 cells), not status rows.

## Finding -> result
- M-1 fixed: CT lane A row A-001 (CT line 511) now gives the Scene 1 to 4 string only, same as RW A-001 and Table 1 row 1; the Scene 5 sentence is named as only in A-001L (RW 500).
- M-2 fixed: CT line 122 is the one place that states 330 = lane A block 100 + Part 7 230, with column sums (21+81, 23+41, 6+9, 39+45, 11+54); mapping RELAYED-ONLY = SUPPORTED ONLY BY RELAYED NUMBER stated at CT 122, CT Part 2 (688), CT Part 7, and RW line 32; the lane A block (CT 613) and Part 7 (CT 1039) now say they count only their own rows.
- M-3 fixed (reviewer right: line 27 is the definition of review): RW A-084 note no longer cites line 27 and the dropped reading (example.com / .test cannot receive e-mail) is removed there; RW line 29 now says no paste string, step or note names the take's domain, and example.com / example.test appear only to say where a file names them. CT row 2 already only cites the files (no change needed).
- M-4 fixed as one meaning, UNANSWERED where the files do not decide: RW glossary (line 204), step 6, steps 11 and 12 and input-table row (i): the prepared send note = ONE script; ONE run posts ONE made-up lead ONCE; the take runs it twice for lead ID 1 (scene 2, scene 3). Files conflict (Q31 item 58 (b) describes a loop that posts twice in one run; steps 11 and 12 need two separate runs because voice sits between the scenes), so row (i) carries an UNANSWERED audit proposal, lead to confirm, with Q31 items 58 and 86.
- M-5 fixed: test run and take defined by named steps. Request 1 = after the test run (P4a step 3, positive control step 4, rehearsal 1 step 6; sent when step 6 ends, new item (g) in step 6); request 2 = after the take (steps 11 to 13; sent in step 16 after step 13a). In RW lines 24, 91, step 6, step 16 and CT lines 12 and 147. The old words "practice run" (line 24, 91) replaced by "the sends of steps 3, 4 and 6"; the Wed 06:00Z practice run of Q30 item 1 is noted as a run whose sends no file lists. New input row (v): the latest delete time is UNANSWERED.
- M-6 fixed: strings of B-219 (post, ONS:131) and B-003b (PLAN:57) now hold only the scoped sentence (B-219: 'The post says only: In this recording, ...'; B-003b: 'In this recording, ... mailbox', replacing the whole quoted list). Clauses 'leads arrive through n8n' and 'n8n is built to write the CRM contact and to send the e-mail message' are removed (still supported readings, CT B-026 to B-028, but not allowed to ship because order 017 allows one result). Both rows no longer wait for P4a themselves (RW 0b P4a row updated); both stay HELD with A-016f. CT lines 302, 707, 975 changed to match.
- M-7 UNANSWERED (needs lead): files disagree (run sheet label 'sped up' kept by N-11a vs step 13 'nothing on screen during the takeover time'). Added input-table row (u) with the written default 'not shown', added N-10 to the list of viewer-facing rows (line 3), notes of N-10, N-11a, N-11b and step 13 point to row (u). No Q31 item exists; the lead adds one.
- M-8 fixed: N-12 tag is now 'Intake mailbox (demo e-mail messages sent by the flow)' (RW 251, CT 668), with a meaning note (not messages from or to a lead).
- M-9 fixed: the wait is in seconds only (step 6 (a)), step 12a says 'in seconds ... floor of 75 seconds plus the margin'; 'recording' = finished video only: 12a and step 15 now say screen capture of this take, and so in the recording.
- M-10 fixed (read in the files, static): RW step 1a names the places: lease = text interval '45 seconds' in field query of node Claim (mf-form.json line 97, mf-hook.json line 97) and node ClaimStuck (mf-recovery.json line 26); 30 s check = node Every30s, field secondsInterval = 30 (mf-recovery.json line 10), folder handover/demo/n8n-flows-real-v5. The lead repeats the read on the take folder after fill_flows; otherwise N-5a, N-5b and step 13 are not used. Still UNVERIFIED for the take folder (not present).
- M-11 fixed (reconciled): steps 5, 7, 9 tags now name the human role of row (o) next to [LEAD]; line 163 rewritten to say the same and to limit 'the lead until another person is named' in steps 10 to 14 to typing and file work; the 'Who acts' default in the intro of 0c reworded. Row (o) stays a BLOCKER.
- M-12 fixed: NO-GO path defined once in RW 0-words (end of the re-pin bullet, line 90): GO or NO-GO answer of Tue 17 Nov 14:00Z (Q26 item 1) or a slip after the rehearsal (ORDERS.md line 156 item 7); only the dates move; re-pin latest Mon 23 Nov 07:00Z = 12:30 IST before credits stop 18:29Z = 23:59 IST (ORDERS.md line 156 item 6).

## Files changed
RUNSHEET-WORDING.md, CLAIMS-TABLE.md, reviews/fix-rwct21.md. Backups of the old files are in the session scratchpad only.

## Raw outputs (run from handover/flows-audit)

$ python3 -I tools/check_rw_ct_pairs.py RUNSHEET-WORDING.md CLAIMS-TABLE.md
```
paste strings in RW: 140 | found word for word in CT: 140
not found in CT: 0
```

$ python3 -I tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md
```
section '3': 74 rows
section '7': 46 rows
total rows: 195
claim ids marked UNSUPPORTED, OVERSTATED, DELETE or STALE in CLAIMS-TABLE.md: 96 | with no row here: []
claim ids marked UNTRACED there: 64 | with no row here: 53 (scope: UNTRACED claims have no safe wording, so they get a row only when a file sentence had to change)
RESULT: PASS
```

$ python3 claims-count.py CLAIMS-TABLE.md
```
verdicts: {'UNSUPPORTED': 15, 'OVERSTATED': 84, 'UNTRACED': 65, 'SUPPORTED': 102, 'RELAYED-ONLY': 64} total 330
lanes (A, B incl. X): {'A': 100, 'B': 226, 'X': 4}
to-do rows: 87
offenders: 0 []
ids: 330 unique: 330
```

$ python3 -I tools/check_refs.py
```
PASS 5176 references
```

$ python3 -I tools/check_names.py
```
PASS 655 rows
```

$ python3 -I tools/check_secrets.py
```
PASS 0 hits in 2072 files
```
