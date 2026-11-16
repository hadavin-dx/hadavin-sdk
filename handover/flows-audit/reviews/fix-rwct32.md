# fix-rwct32: one pass on RUNSHEET-WORDING.md (RW) and CLAIMS-TABLE.md (CT), from read r32 (and r22 recheck)
Editor: this agent only. Static, made-up data, no secrets printed. Not committed. EGM: this is an edit pass on the two files from a review; the lead runs the EGM result review (I did not invoke EGM skills). Rules used: R-numbers not looked up (bible not in this checkout; not checked).

## What I did not do or could not check (first)
- B2 (nobody named for voice, screen capture, mailbox emptying, window arranging; scene 4 stop script; typed answers have no scene): needs the lead/owner; not fixable by me. Question lines below.
- I did not run any flow, send or test; everything is read from files. The second-send item (reply of POST 2 with repeat true) is read in demo/n8n-flows-real-v5/mf-form.json line 293, not run.
- r22 item 1 (give N-5a a CT lane row) not done: a new claim id changes the 330 total and every count check; question line below. Everything else in r22 was already fixed or is fixed here (checked below).
- Reviewer line numbers were approximate; I located every item by text.

## B1 and M12 (A-016a/b/f/h, step 15, CT A-099/A-100)
Problem confirmed in the text: the one scoped sentence says "sent twice" but step 15 itself said the attempts column does not show a second send and left the on-screen item "NOT WRITTEN".
Choice (safest): keep the sentence word for word (order 017 fixes it) and keep A-016b, A-016f, A-016h HELD with a named item that must be IN FRAME in the same recording: (i) the reply of POST 2 with field repeat showing true (mf-form.json real-v5 line 293: repeat carries true, stored state in verdict; only reply time stays outside the proof), or (ii) the n8n run list with two runs for the lead ID (needs saving on, F-008, row A-007). Neither in frame = A-016a/b/f/h not used. It is kept as a separate condition so "two-part proof" (mailbox count, mf_leads row) keeps its meaning. A-016a (PASTE, string unchanged) now carries the same condition in its note, in the line-3 summary and in CT A-016; the narrower sentence is NOT applied.
Edited: RW line 3, A-016a, A-016b, A-016f, A-016h, step 15 (NOT WRITTEN block replaced by SECOND-SEND ITEM; marking condition); CT A-016 and A-099 (A-099 verdict stays UNTRACED: no recording yet).
Which item the take screens show: still NOT WRITTEN: LEAD FILLS (take scripts not in this checkout).

## Other findings
- M3 first use: new 0-words bullet "first use of a word by a viewer". N-12 viewer string no longer says "sent by the flow" (now "Intake mailbox (demo e-mail messages that arrive here)", RW and CT). A-007 string now names n8n and what it is ("n8n, the program that runs the steps of this demo, lists the runs it saved. ..."), RW and CT (2 places). flow and lead table stay out of viewer strings before scene 4 (N-5a explains flow and lead); lead ID is explained by A-016d first.
- M4 label need: step 12a new (5), input row (m), A-044a scope note: the six-column preview shows mail sent and alert sent; mail_sent is set before the mail step runs, so the A-044a label ("mail sent means the mail step was started") goes beside the column in scene 3 too, or the column is left out of the frame. alert sent has no label: left out of frame or label written (lead fills).
- M5 V-11: I checked it: mf-sub-crm-mail.json real-v5 line 103 holds HS_CRED_PLACEHOLDER and V5-NODE-DIFF.txt shows the change from HUBSPOT_CREDENTIAL_ID. So V-11 stays, now stated as checked (note), CT B-175 evidence and a paste pointer added; step 1b item (3) no longer says "reported by a reviewer, not checked".
- M6 "keyed on e-mail" is now "built to be keyed ... (as configured, not observed)" in A-012, A-016a, A-016c, A-016g, step 15, B-010 note, B-147 paste (RW and CT), CT evidence cells (B-147, A-012 flow path text), CT A-101.
- M7 A-012 vs steps 8/11: R:31 is stated to be a line of the run sheet file, not filmed, spoken or posted; the count 1 there is the lead's expected value; if that file is ever on screen A-012 is not applied (added to A-012, step 8, step 11). Whether the file is ever filmed: question line.
- M8 send count: now "at least SEVEN made-up lead IDs" (five scene lead IDs plus the two control messages of step 4, which reach the stage service when sent through the flows) plus the unknown practice run sends, in RW lines 24, 71, 170, 507 and the ceiling row (k). The cap number is still not invented (Q31 item 3).
- M9 crossed A-043/A-044: swapped the paste pointers in CT (CT A-043 row, claim "mail_sent true", now points to RW A-044a/A-044b; CT A-044 row, the old caption, now points to RW A-043); pointer sentences added in both RW rows.
- M10: CT pointers added to B-150 (for B-150c), B-165, B-182 (RW string wins where CT note differs).
- M11: B-145 "1 s": CT evidence cell now cites mf-sub-crm-mail.json line 37 (waitBetweenTries 1000) in real-v5 and film-v5 (read). B-155 "per stage": SendMail has retryOnFail false in real-v5 (read), so the paste string is now "built with 2 tries for the stage service step and the CRM step, 10 s each except the real CRM step, which sets no time limit; the mail step is tried once" (RW and CT).
- IST: APPROVED blank shape now has the IST time in brackets with a made-up example (08:20Z = 13:50 IST); RW line 91 "06:00Z" now has IST. A scan for UTC times without IST within 45 characters found only the example and two CT definition lines that give IST in the same sentence.
- r22 recheck: items 2 (speed-up rule, row (u) and N-10), 3 (A-008a string), 4 (B-195/B-197 "reported ... not seen raw files"), 5 (delete request steps), 6 (counts) and 9 (S9) are already fixed in the current text (read). Lower items not touched.

## Check results (run from flows-audit, after the edits)
check_refs.py: PASS 5178 references | check_names.py: PASS 655 rows | check_secrets.py: PASS 0 hits in 2730 files | check_rw_ct_pairs.py: paste strings in RW 142, found word for word in CT 142, not found 0 | check_runsheet_paste.py: total rows 197, RESULT: PASS | claims-count.py: SUPPORTED 102, OVERSTATED 84, UNTRACED 65, UNSUPPORTED 15, RELAYED-ONLY 64, total 330; lanes A 100, B 226, X 4; offenders 0; ids 330 unique | check_counts.py: PASS 52 files / 655 nodes | ruff format --check .: 877 files already formatted (was 874 before; the 3 extra files are not mine).
Row statuses and counts unchanged (no status changed).

## Question lines for QUESTIONS.md (for the lead; I did not edit it)
- NQ-A (B2, Q31 item 100): name the people for voice rows, the screen capture, emptying the intake mailbox, arranging windows. Also: the typed answers y, the challenge number and "end" have no scene or step that says when they are typed.
- NQ-B (row (r), Q31 item 105): the scene 4 stop script, what triggers it and when it falls are still not written.
- NQ-C (B1): which second-send item is in frame in the take: the reply of POST 2 (repeat true) or the n8n run list (needs F-008 saving on)? If neither, do you re-film or give a narrower sentence such as "In this recording, the intake mailbox shows one e-mail message for the lead ID."? (not applied; order 017 fixes the one sentence).
- NQ-D (M7): is the run sheet file (R:31 and others) ever on screen? If yes, A-012 is not applied.
- NQ-E (M4): in scene 3 do you place the A-044a label beside the column mail sent, or leave the column out of the frame? Same for alert sent: leave out, or write a label.
- NQ-F (r22 item 1): do you want a CT lane row for N-5a (it changes the 330 total and all counts)?
