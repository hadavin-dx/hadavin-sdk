# v10 CHANGES: every finding and where it is fixed

Day sheet = OWNER-STEPS-realrun-v10.md (240 lines, many long; the target of about 200 is NOT met, see NOTES). Appendix = OWNER-STEPS-v10-APPENDIX.md. Locations are section labels (line numbers drift). Sources: SecM/SecN = review-v9-security.md; NvB/NvM = review-v9-naive.md blockers and majors; Cit = citation-check-v9.md; Dir = the coordinator brief's specific directions; Q15.x = lead answer of 10:13 UTC.

NOT FIXED items first: none are left unfixed as text. Items that depend on facts I could not verify are written as go conditions or as an unverified note and are listed in v10-NOTES-FOR-LEAD.md: SecM4 (program deletes contacts), SecN python3 -I, NvM5 HubSpot search, NvB2 real notice layout.

| Id | Where fixed in v10 | Status |
|---|---|---|
| SecM1 one money rule | day sheet "The money rule": balance check (balance >= run total) separate from backstop check (backstop <= money used so far + run total); step A.3 and F.2 and I.0 point to it | fixed (rule is my design: NOTES Q1) |
| SecM2 emergency cancel | money rule last bullet: cancel needs no message from the studio lead; I.0 normal path waits for "model program stopped" and "no more runs" | fixed |
| SecM3 owner makes key | A.0: owner creates a run-only key, saves it in the row 8 file, sends only key name and path; studio lead never makes or receives it | fixed (NOTES Q2: new key vs the saved one) |
| SecM4 program deletes contacts | go condition 5 (written statement); F.1 stop if any line says delete or archive; self-contradicting sentence removed; appendix section 8 states the scope-sheet conflict | fixed as go condition; UNVERIFIED program fact |
| SecM5 n8n connection values | go condition 4 (written, lead removes any model credential) and C.3 (owner looks at the credentials list, names only, exactly two, none opened) | fixed |
| SecM6 time-of-check | go condition 6 (restart time UTC and IST) and E.0 (re-read the two setting lines just before start) | fixed |
| SecM7 setting names | rule 10: names only A-Z 0-9 _ and no KEY/TOKEN/SECRET/PASSWORD, else stop; A.1 uses one `grep -E '^<name>='` per name (no `|` in the pattern) | fixed |
| SecN counting greps | step 0.5 uses `grep -c` and `grep -oE ... \| grep -vc`; owner reports counts; no printing grep | fixed |
| SecN cat shows secret | the secret-showing copy procedure moved to appendix section 7, `clip.exe` named as unchecked | fixed (by moving and warning) |
| SecN symlink check final component only | rule 10 and I.6: `readlink -f` must equal the typed path, `ls -ld` on the secret folder | fixed (needs `readlink` on the laptop: unverified) |
| SecN rule 11 omits n | rule 11 lists `n` | fixed |
| SecN python3 without -I | every `python3` now `python3 -I` (checked by scan: 0 without -I) | fixed; whether the programs run under -I is UNVERIFIED (NOTES Q6) |
| SecN "at most 3 paid calls" | reworded to "planned 3 paid model calls" in notice, yes sentence, warning | fixed |
| SecN "nothing is sent" at n | "The program sends nothing and ends" in Do this first, warning before E | fixed |
| SecN usage pages lag | money rule: read at F.2 and again before cancelling; largest figure counts | fixed |
| SecN E.3 "throwaway confirmed" adds no information | C.4 says the reply only shows the message arrived; check is the owner's; program does not show the accounts | fixed |
| SecN "at most 3 runs in all" ambiguous | I.4: "At most 3 runs of it in all, counting every run whatever the outcome" | fixed |
| SecN filter passes names/ids without @ | 0.5: owner reads the file himself, sends only PASS/FAIL/SKIPPED lines; text says the filter does not catch names or numbers | fixed |
| SecN decision 7 narrower | C.3 no longer copies values; old procedure only in appendix 7 | fixed |
| NvB1 sender Gmail | Do this first item 1, go condition 1, row 17; the studio lead decides if it does not exist | fixed; open fact NOTES Q3 |
| NvB2 notice never shown | E.2 made-up sample notice (clearly labelled invented) | fixed; replace by the real notice after the rehearsal |
| NvB3 y left waiting; E.3 before E.1 | former E.3 is now C.4 (before the go and before E.1); E.0 says the start clock keeps running; E.3 `y` at once | fixed |
| NvB4 sender sign-in, profile, 2-step | C.4: normal profile (not `demo-take`), sender sign-in with 2-step on the phone, sign out | fixed |
| NvB5 exit 3 vs C unknown | go condition 7 and J: lead states in writing which exit codes count as success | fixed |
| NvB6 n8n Claude credential | go condition 4: the studio lead removes it and says so; owner looks at the list (C.3) | fixed |
| NvB7 proof screen who films | step D item 5: studio lead makes it from the rehearsal, row 4 editor adds it, owner films nothing | fixed |
| NvM1 filter false alarms; lead cannot see | 0.5: owner looks, reports "key-like" or "harmless, kind" | fixed |
| NvM2 placeholders, `|` in patterns | Words: placeholder rule; made-up filled example after rule 12; one name per grep | fixed |
| NvM3 17 rows vs "if missing" | run card intro: a go needs all 17; a card with a missing row is incomplete | fixed |
| NvM4 word clashes | "exit code" only; result files named three ways (appendix 1); "the step 0 program", "the program", "the model program"; "the real run"; check vs test defined; "portal" only in appendix; HubSpot "account number" | fixed |
| NvM5 F.1 no time limit; search; "to archive" | F.1: row 12 now also gives the longest film pause; fallback look by create date (marked unchecked); delete/archive line = stop | fixed; HubSpot search UNVERIFIED |
| NvM6 address bar number | step D item 8: default is the editor crops the address bar | fixed |
| NvM7 calculator heavy | kept (binding money check), compressed to A.2; tension with the owner's 2026-11-15 "no limit questions": NOTES Q4 | kept deliberately |
| NvM8 who runs the 13 sends | E "What is normal": the program makes them | fixed |
| NvM9 I.0 before video accepted | I.0 triggers on the studio lead's "model program stopped" and "no more runs"; re-key path if the video is rejected | fixed |
| NvM10 wrong confirmation burns name | E.4: marker only after a correct line; lead says whether the name can be reused | fixed (marker timing from scope sheet) |
| NvM11 I.4 cases table | I.4 table | fixed |
| NvM12 two Ubuntu windows | E.0: second window beside the run window, `echo SECOND WINDOW` typed in it before start | fixed |
| Order | "Order of the day" and "Do this first" at the top; day order of sections (A, B-D, E, F, T/G, I.0, H, I, J); sha256sum of the program moved into E.0 | fixed |
| Labels before definition | "Words you need first" defines lead desk, studio lead, real run, go message, step 0 program, n8n, notice, exit code | fixed |
| UTC/IST gaps | every time shows both halves (checked by scan for "IST" next to each UTC time); the posting aim "Wed 18 Nov" is date-only and now stated as aim only in the order, not as a time | fixed; see NOTES Q5 |
| Length | step table, ban list, exit codes, studio-lead list, glossary moved to the appendix (nothing dropped); sheet 411 -> 240 lines | PARTLY: target 180-200 not reached |
| Nits: internal codes | BL-wp6-G1, S9-x only in the studio-lead section 8, marked as design item names | partly kept (studio lead only) |
| Nit: "laptop does not enforce it" alarming | reworded in "How messages fit": it is the studio lead's rule, the laptop cannot enforce it, so you create and cancel the key | fixed |
| Nit: L5 vs L190 type nothing vs close terminal | Do this first and step 0 stop lists separate: step 0 closes the window; elsewhere type nothing | fixed |
| Nit: `<your-user>` literal | "Words" placeholder rule; I.3 says `<your user name>` | fixed |
| Nit: J one table / long item | J split: day sheet content, ban list in appendix 5 | fixed |
| CitC1 "60.1 to 61.9" / cut number | appendix 8 last bullet has no number | fixed |
| CitC2 missing 0.0 heading | "0.0 Go." added | fixed |
| CitC3 post-by date source | J heading: date taken from the earlier sheet, studio lead confirms on row 7 | fixed as a labelled assumption |
| CitC4 backstop vs credit | money rule and appendix 1 keep backstop (US$180) and credit (US$189) separate | fixed |
| Dir: reword "at most 3" | see SecN | fixed |
| Dir: made-up sample notice | E.2 | fixed |
| Dir: define every label | Words section | fixed |
| Q15.2 clean start | day sheet line after "Order of the day"; go condition 9; appendix step table row 2 (owner of the row: the studio lead) | added as the lead said |
| Q15.3 lease sentence | day sheet E "What is normal" and J, appendix 5 and 8: "a lead sent twice with the same id inside the lease is processed once" | added |
| Q15.4 spend limit | money rule and appendix 8: owner's own eye plus the model program's stage checks; no hard cap claimed | added |
