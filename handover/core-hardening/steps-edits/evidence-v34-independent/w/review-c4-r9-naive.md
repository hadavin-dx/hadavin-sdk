# EDITS round 9 naive-reader review (egm-comprehension, condensed copy of the inline report), 2026-11-16
Target: steps-edits/EDITS.md (827 lines, 52 rows). Verdict: 2 blockers, 13 majors, many minors. Reader opened only EDITS.md and the persona file.

## BLOCKERS
- B1 E-11 (lines 253-266): the owner's "ok" checks only the key file, not the model address, though a wrong address is the paid call. "a control that does not depend on anyone's care" is false (it depends on the assistant naming the right address and the owner reading it). "starts with 127.0.0.1" lets 127.0.0.1.example.com pass: say exactly 127.0.0.1 plus a port. No reply is given for "the file IS the real one" or "address is wrong". Fix: owner condition covers address and file; state the refusal reply; drop the claim.
- B2 E-09 (lines 236-251): step d chmod 600 does not hide the file from the assistant (same Linux user, clipboard, screen), so step a is a promise, not a control: say so. ND1 default (a) says the password is a line in n8n.env, step b says new empty file, step f says "another file"; how the content reaches n8n.env or the database is not said. Step f's "n8n form for this Postgres credential" is a fourth credential while E-37 says three. Line 34 says E-09 falls away if v4 drops step 8, but E-09 is the only place that tells how to make the password file. Step a needs a "you may look again" signal; steps a-e must happen before the database starts.

## MAJOR
- M1 "studio lead" never defined (person or Claude session); "the lead" used in E-26, E-31, E-38, E-53 headers; EL-1..EL-7 is another sense; line 16 "five older meanings" is wrong; "the builder", "the runner" undefined.
- M2 "yes message" means the assistant's request (E-12, E-37, E-52) and the owner's reply (E-14 line 306).
- M3 E-12 (lines 268-286): the yes cannot be typed as shown (one long line vs "one short line each"; placeholders N1, N2, <take id>, <file>, <X>; closing sentence required or not; crash check untested has no slot; latest start 18:14 UTC on 23 Nov presented as fact though UNVERIFIED (line 22); take planned Wed 18 Nov so the latest start that day is not stated; 23 Nov not said to be the LAST day).
- M4 E-37 line 568: what is one line and what is a separate Enter (y, 6-digit number, space, take id, then end).
- M5 E-48 (lines 682-696): last time to revoke 18:19 UTC is 10 minutes before the money stop, a take started at 18:14 cannot be cleaned up by then; "cancel" vs "revoke"; on "no"/"not sure" the live key's copy is removed by plain rm only (ND9 discusses only the n8n key); shred -u without saying where the files are; "receiver password file" undefined; question text differs from ND7a; ND7 reply codes (7a: yes) are internal.
- M6 E-16 (lines 321-330): removing the database container destroys both n8n's database and the take's table; no step saves results first; how the container is identified; "before you sign off" undefined; no exact reply for the yes/no question.
- M7 E-39 (lines 583-592): round-6 (b) vs round-9 (b) conflict; the round-9 (b) adds deleting the 3 credentials in n8n, which appears in no decision; new text only for answer (b) though R4 says per answer.
- M8 v3 "archived, never edited" vs Apply-now edits (lines 34, 26, 52): which file does the owner read?
- M9 Words with several meanings: app (app password, HubSpot private app 1/2, app schema, app user/role, n8n account), window (spending window, WSL window, closing the window, crash windows, window end; E-51 new text still says "window end" though E-52 renames it), screen (display, film shot, chat, program output), post (publish, send to n8n, "person C is posted"), address, round (drafting rounds vs fix rounds).
- M10 E-03/E-52 say both tests planned at US$0; E-11 says flow rehearsal cost not confirmed.
- M11 ND6 option B reply names an undefined "preparation test" in a money consent sentence (elsewhere "preparation enquiry").
- M12 E-12 tells the owner to expect "no delete call" while held E-05/E-41/E-42 leave v3 lines 95, 103, 104 saying "archived"; E-04 (3) asks the owner to tell which app the secret key belongs to (shows key on shared screen); "contact number" vs "contact id".
- M13 "re-pin" never defined (lines 27, 148, 411).

## MINOR (grouped)
Terms before definition (Hold rows, HOLD Gx line 12; E-nn; "Apply now" can read as an instruction to the owner; NEEDS-STUDIO-LEAD and Conditional not in index); "rehearsal" alone (lines 19, 46, 808); undefined terms (egm:*, r17 review, C4b, evidence-2, INDEX, S9-n, smk_n8n, person A/B/C, receiver, first smoke, stage settings file, search path, EG, N8N_DISABLED_MODULES); role vs database user; "credentials of their own" vs E-52 definition; E-20 still says "saved passwords"; cancel/revoke; key meanings; E-07/E-08 "Linux window" wrong, E-08 "nobody has read" vs ND5 "nobody on this branch"; E-13 has two OLD blocks and no NEW block (line 12 says every Hold row has one); E-14 line 306 contradictory film guidance, who decides footage; E-17 Why describes identical phrase and public post uses "the take's database"; E-31 "failed read stops the take safely" unproven; E-36 Why last sentence circular; ND8 option A lists a path that cannot send one enquiry; E-49/E-50 `<day>` format; E-04 line 188 unfinished sentence; E-37 heading date vs 23 Nov window confusable; line 40 record format differs from the ND "Record:" lines.

## Row contradictions listed by reviewer
E-09 vs ND1; E-09 f vs E-37; E-03 vs E-11; E-48 vs E-12/E-52; E-12 vs held E-05/E-41/E-42; E-39 (b) round 6 vs round 9; E-51 vs E-52; line 34 vs lines 26/52; E-12 vs E-22 vs E-17 (three phrasings of crash check untested).

## Checked and consistent (reviewer)
Row counts of lines 36-37 (34/14/4 files; 40 Apply now, 12 Hold; STALE 15, UNCLEAR 10, MISSING 14, CONTRADICTION 12, DEFERRED 1); UTC/IST pairs (18:29 = 23:59, 18:19 = 23:49, 18:14 = 23:44); E-24 count (13 live + 4 added = 17, item 10 removed).
